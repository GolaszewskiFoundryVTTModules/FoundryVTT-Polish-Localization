import { mkdirSync, existsSync, readdirSync, rmSync, cpSync, statSync, readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { CONFIG_FILE, readJSONFile } from './config_helper.js';
import ProgressBar from 'progress';
import SftpClient from 'ssh2-sftp-client';
import 'dotenv/config';

const STATIC_PATHS = [
    'LICENSE',
    'module.json',
    'README.md',
    'fonts',
    'lang',
    'style.css',
];

function validateJsonFiles(paths) {
    console.log('Validating JSON files...');
    let allValid = true;
    for (const path of paths) {
        if (statSync(path).isDirectory()) {
            for (const file of readdirSync(path, { recursive: true })) {
                if (file.endsWith('.json')) {
                    try {
                        readJSONFile(join(path, file));
                    } catch (error) {
                        console.error(`\nError: Invalid JSON file found: ${join(path, file)}`);
                        console.error(error.message);
                        allValid = false;
                    }
                }
            }
        } else if (path.endsWith('.json')) {
            try {
                readJSONFile(path);
            } catch (error) {
                console.error(`\nError: Invalid JSON file found: ${path}`);
                console.error(error.message);
                allValid = false;
            }
        }
    }

    if (allValid) {
        console.log('All JSON files are valid.');
    }
    return allValid;
}

// --- Pre-build Validation ---
if (!validateJsonFiles(STATIC_PATHS)) {
    console.error('\nBuild failed due to invalid JSON files. Please fix the errors above and try again.');
    process.exit(1);
}

// Initialize ProgressBar
const bar = new ProgressBar('  Building [:bar] :percent :etas', {
    complete: '=',
    incomplete: ' ',
    width: 40,
    total: STATIC_PATHS.length,
});

let targetFolder = process.argv[2];
if (!targetFolder && existsSync(CONFIG_FILE)) {
    targetFolder = readJSONFile(CONFIG_FILE).buildPath;
}
if (!targetFolder) {
    targetFolder = 'foundryvtt-polish-localization';
}

// Ensure target folder exists and is clean
if (existsSync(targetFolder)) {
    rmSync(targetFolder, { recursive: true, force: true });
}
mkdirSync(targetFolder, { recursive: true });

console.log(`Building to target directory: ${targetFolder}`);

// --- Main Copy Logic ---

for (const path of STATIC_PATHS) {
    if (!existsSync(path)) {
        console.warn(`\nWarning: Source path not found, skipping: ${path}`);
        bar.tick();
        continue;
    }

    const targetPath = join(targetFolder, path);

    try {
        const parentDir = statSync(path).isDirectory() ? targetPath : dirname(targetPath);
        if (!existsSync(parentDir)) {
            mkdirSync(parentDir, { recursive: true });
        }
        cpSync(path, targetPath, { recursive: true });
    } catch (error) {
        console.error(`\nError processing path ${path}:`, error);
    }

    bar.tick();
}

console.log('\nBuild completed!');

// --- Upload to Server (if configured) ---
async function uploadToServer() {
    const sftpConfig = {
        host: process.env.FTP_HOST,
        user: process.env.FTP_USER,
        password: process.env.FTP_PASSWORD,
        remotePath: process.env.FTP_REMOTE_PATH,
    };

    // Check if SFTP upload is enabled via buildconfig.json
    let uploadEnabled = false;
    if (existsSync(CONFIG_FILE)) {
        const config = readJSONFile(CONFIG_FILE);
        uploadEnabled = config.sftp?.enabled === true;
    }

    if (!uploadEnabled) {
        console.log('SFTP upload disabled in buildconfig.json. Skipping upload.');
        return;
    }

    if (!sftpConfig.host || !sftpConfig.user || !sftpConfig.password || !sftpConfig.remotePath) {
        console.warn(
            '\x1b[33mWarning: SFTP upload enabled but environment variables (FTP_HOST, FTP_USER, FTP_PASSWORD, FTP_REMOTE_PATH) are not fully configured.\x1b[0m'
        );
        console.log('Please set the required environment variables to enable SFTP upload.');
        return;
    }

    const client = new SftpClient();
    const remoteModulePath = `${sftpConfig.remotePath}/foundryvtt-polish-localization`;

    try {
        console.log(`\n--------------------------\nConnecting to SFTP server: ${sftpConfig.host}\n--------------------------`);
        await client.connect({
            host: sftpConfig.host,
            port: 22,
            username: sftpConfig.user,
            password: sftpConfig.password,
        });
        console.log('SFTP connection successful.');

        // Smart sync: compare and upload only changes
        await smartSync(client, targetFolder, remoteModulePath);
        
        console.log('\x1b[32m✓ Module successfully synchronized to server!\x1b[0m');
    } catch (err) {
        console.error(`\x1b[31mSFTP Error: Could not upload module. Details: ${err.message}\x1b[0m`);
    } finally {
        if (client.sftp) {
            await client.end();
            console.log('SFTP connection closed.');
        }
    }
}

async function smartSync(client, localDir, remoteDir) {
    const syncStartTime = Date.now();
    console.log('\n' + '='.repeat(60));
    console.log('Starting intelligent sync...');
    console.log('='.repeat(60));
    
    // Get local files structure
    console.log('\n📂 Scanning local files...');
    const localFiles = new Map(); // path -> {size, mtime}
    let localFileCount = 0;
    let localDirCount = 0;
    
    function scanLocal(dir, basePath = '') {
        const entries = readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
            const localPath = join(dir, entry.name);
            const relativePath = basePath ? `${basePath}/${entry.name}` : entry.name;
            
            if (entry.isDirectory()) {
                localDirCount++;
                scanLocal(localPath, relativePath);
            } else {
                localFileCount++;
                const stats = statSync(localPath);
                localFiles.set(relativePath, {
                    size: stats.size,
                    mtime: stats.mtimeMs,
                    fullPath: localPath
                });
                
                // Show progress every 50 files
                if (localFileCount % 50 === 0) {
                    process.stdout.write(`\r  Found ${localFileCount} files in ${localDirCount} directories...`);
                }
            }
        }
    }
    scanLocal(localDir);
    console.log(`\r  ✓ Scanned ${localFileCount} files in ${localDirCount} directories`);

    // Get remote files structure
    const remoteExists = await client.exists(remoteDir);
    const remoteFiles = new Map(); // path -> {size, mtime}
    let remoteDirCount = 0;
    
    if (remoteExists) {
        console.log('\n🌐 Scanning remote files...');
        let remoteFileCount = 0;
        
        async function scanRemote(dir, basePath = '') {
            try {
                const entries = await client.list(dir);
                remoteDirCount++;
                
                for (const entry of entries) {
                    const relativePath = basePath ? `${basePath}/${entry.name}` : entry.name;
                    const remotePath = `${dir}/${entry.name}`;
                    
                    if (entry.type === 'd') {
                        await scanRemote(remotePath, relativePath);
                    } else {
                        remoteFileCount++;
                        remoteFiles.set(relativePath, {
                            size: entry.size,
                            mtime: entry.modifyTime
                        });
                        
                        // Show progress every 50 files
                        if (remoteFileCount % 50 === 0) {
                            process.stdout.write(`\r  Found ${remoteFileCount} files in ${remoteDirCount} directories...`);
                        }
                    }
                }
            } catch (err) {
                // Directory might not exist, skip
            }
        }
        await scanRemote(remoteDir);
        console.log(`\r  ✓ Scanned ${remoteFiles.size} files in ${remoteDirCount} directories`);
    } else {
        console.log('\n🌐 Remote directory does not exist. Will create on first upload.');
        await client.mkdir(remoteDir, true);
    }

    // Compare and determine actions
    console.log('\n🔍 Comparing local and remote files...');
    const toUpload = [];
    const toDelete = [];
    const newFiles = [];
    const modifiedFiles = [];

    // Check what needs to be uploaded (new or modified)
    for (const [relativePath, localInfo] of localFiles) {
        const remoteInfo = remoteFiles.get(relativePath);
        
        if (!remoteInfo) {
            // File doesn't exist on remote
            toUpload.push(relativePath);
            newFiles.push(relativePath);
        } else if (localInfo.size !== remoteInfo.size) {
            // File size differs - needs update
            toUpload.push(relativePath);
            modifiedFiles.push(relativePath);
        }
    }

    // Check what needs to be deleted (exists on remote but not local)
    for (const relativePath of remoteFiles.keys()) {
        if (!localFiles.has(relativePath)) {
            toDelete.push(relativePath);
        }
    }

    const unchangedCount = localFiles.size - toUpload.length;
    
    console.log('\n' + '='.repeat(60));
    console.log('Sync Plan:');
    console.log('='.repeat(60));
    console.log(`  📤 Files to upload: ${toUpload.length}`);
    console.log(`     ├─ New files: ${newFiles.length}`);
    console.log(`     └─ Modified files: ${modifiedFiles.length}`);
    console.log(`  🗑️  Files to delete: ${toDelete.length}`);
    console.log(`  ✅ Files unchanged: ${unchangedCount}`);
    console.log('='.repeat(60));

    // Delete obsolete files
    if (toDelete.length > 0) {
        console.log(`\n🗑️  Deleting ${toDelete.length} obsolete files...`);
        const deleteBar = new ProgressBar('  Deleting [:bar] :percent :current/:total', {
            complete: '=',
            incomplete: ' ',
            width: 40,
            total: toDelete.length,
        });
        
        let deleteErrors = 0;
        for (const relativePath of toDelete) {
            const remotePath = `${remoteDir}/${relativePath}`;
            try {
                await client.delete(remotePath);
                deleteBar.tick();
            } catch (err) {
                deleteErrors++;
                deleteBar.tick();
            }
        }
        
        if (deleteErrors > 0) {
            console.log(`  ⚠️  ${deleteErrors} files could not be deleted`);
        }
    }

    // Upload new/modified files
    if (toUpload.length > 0) {
        console.log(`\n📤 Uploading ${toUpload.length} files...`);
        const uploadBar = new ProgressBar('  Uploading [:bar] :percent :current/:total :etas', {
            complete: '=',
            incomplete: ' ',
            width: 40,
            total: toUpload.length,
        });

        let uploadErrors = 0;
        let uploadedBytes = 0;
        
        for (const relativePath of toUpload) {
            const localInfo = localFiles.get(relativePath);
            const remotePath = `${remoteDir}/${relativePath}`;
            
            // Ensure remote directory exists
            const remoteFileDir = dirname(remotePath);
            await client.mkdir(remoteFileDir, true);
            
            try {
                await client.fastPut(localInfo.fullPath, remotePath);
                uploadedBytes += localInfo.size;
                uploadBar.tick();
            } catch (err) {
                uploadErrors++;
                uploadBar.tick();
            }
        }
        
        const uploadedMB = (uploadedBytes / (1024 * 1024)).toFixed(2);
        console.log(`  ✅ Uploaded ${uploadedMB} MB`);
        
        if (uploadErrors > 0) {
            console.log(`  ⚠️  ${uploadErrors} files failed to upload`);
        }
    } else {
        console.log('\n✅ No files to upload - everything is up to date!');
    }
    
    // Summary
    const syncDuration = ((Date.now() - syncStartTime) / 1000).toFixed(2);
    console.log('\n' + '='.repeat(60));
    console.log(`Sync completed in ${syncDuration}s`);
    console.log('='.repeat(60));
}

// Run upload if configured
uploadToServer().catch((err) => {
    console.error(`\x1b[31mUpload failed: ${err.message}\x1b[0m`);
    process.exit(1);
});
