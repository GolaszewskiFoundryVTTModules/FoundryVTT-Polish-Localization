import SftpClient from 'ssh2-sftp-client';
import { mkdirSync, existsSync, rmSync, writeFileSync } from 'fs';
import { join } from 'path';
import 'dotenv/config';

/**
 * Downloads source localization files from SFTP server
 */
async function downloadSourceFiles() {
    const sftpConfig = {
        host: process.env.FTP_HOST,
        user: process.env.FTP_USER,
        password: process.env.FTP_PASSWORD,
        remotePath: process.env.FTP_SOURCE_PATH || process.env.FTP_REMOTE_PATH,
    };

    if (!sftpConfig.host || !sftpConfig.user || !sftpConfig.password || !sftpConfig.remotePath) {
        console.error(
            '\x1b[31mError: Environment variables (FTP_HOST, FTP_USER, FTP_PASSWORD, FTP_SOURCE_PATH) are not configured.\x1b[0m'
        );
        console.log('Please create a .env file with the required SFTP credentials.');
        process.exit(1);
    }

    const localDownloadPath = './downloaded-source';
    const client = new SftpClient();

    // Clean and create download directory
    if (existsSync(localDownloadPath)) {
        rmSync(localDownloadPath, { recursive: true, force: true });
    }
    mkdirSync(localDownloadPath, { recursive: true });

    const log = {
        timestamp: new Date().toISOString(),
        downloaded: [],
        errors: [],
    };

    try {
        console.log(`\n${'='.repeat(60)}`);
        console.log(`Connecting to SFTP server: ${sftpConfig.host}`);
        console.log('='.repeat(60));
        
        await client.connect({
            host: sftpConfig.host,
            port: 22,
            username: sftpConfig.user,
            password: sftpConfig.password,
        });
        console.log('✓ SFTP connection successful.\n');

        // Determine if remotePath is a file or directory
        const isFile = sftpConfig.remotePath.endsWith('.json');
        
        let remoteEnPath;
        
        if (isFile) {
            // Direct file path provided
            console.log(`ℹ️  Source path points to a file: ${sftpConfig.remotePath}`);
            remoteEnPath = sftpConfig.remotePath;
        } else {
            // Directory path provided
            console.log(`ℹ️  Source path is a directory: ${sftpConfig.remotePath}`);
            remoteEnPath = `${sftpConfig.remotePath}/en.json`;
        }

        // Download en.json (source file)
        const localEnPath = join(localDownloadPath, 'en.json');

        try {
            console.log(`📥 Downloading: ${remoteEnPath}`);
            await client.fastGet(remoteEnPath, localEnPath);
            console.log(`✓ Saved to: ${localEnPath}`);
            log.downloaded.push({
                remote: remoteEnPath,
                local: localEnPath,
                success: true,
            });
        } catch (error) {
            console.error(`\x1b[31m✗ Error downloading ${remoteEnPath}: ${error.message}\x1b[0m`);
            log.errors.push({
                file: remoteEnPath,
                error: error.message,
            });
        }

        console.log(`\n${'='.repeat(60)}`);
        console.log(`Download Summary:`);
        console.log(`  ✓ Downloaded: ${log.downloaded.length} files`);
        console.log(`  ✗ Errors: ${log.errors.length}`);
        console.log('='.repeat(60));

    } catch (err) {
        console.error(`\x1b[31mSFTP Error: ${err.message}\x1b[0m`);
        log.errors.push({
            file: 'connection',
            error: err.message,
        });
        process.exit(1);
    } finally {
        if (client.sftp) {
            await client.end();
            console.log('\n✓ SFTP connection closed.');
        }
    }

    // Write log file
    const logPath = join(localDownloadPath, 'download-log.json');
    writeFileSync(logPath, JSON.stringify(log, null, 2));
    console.log(`\n📄 Log saved to: ${logPath}`);

    if (log.errors.length > 0) {
        console.log('\n\x1b[33m⚠️  Some files could not be downloaded. Check the log for details.\x1b[0m');
    } else {
        console.log('\n\x1b[32m✓ All files downloaded successfully!\x1b[0m');
    }
}

// Run the download
downloadSourceFiles().catch((err) => {
    console.error(`\x1b[31mFatal error: ${err.message}\x1b[0m`);
    process.exit(1);
});
