const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = 3000;
const HOST = 'localhost';

const mimeTypes = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.gif': 'image/gif',
    '.ico': 'image/x-icon',
    '.svg': 'image/svg+xml'
};

function serveFile(filePath, res) {
    fs.readFile(filePath, (err, content) => {
        if (err) {
            if (err.code === 'ENOENT') {
                res.writeHead(404, { 'Content-Type': 'text/plain' });
                res.end('File not found');
            } else {
                res.writeHead(500, { 'Content-Type': 'text/plain' });
                res.end('Server error: ' + err.message);
            }
        } else {
            const ext = path.extname(filePath);
            const contentType = mimeTypes[ext] || 'text/plain';
            
            res.writeHead(200, { 
                'Content-Type': contentType,
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            });
            res.end(content);
        }
    });
}

const server = http.createServer((req, res) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
    
    // Handle CORS preflight requests
    if (req.method === 'OPTIONS') {
        res.writeHead(200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        });
        res.end();
        return;
    }
    
    const parsedUrl = url.parse(req.url);
    let filePath = path.join(__dirname, parsedUrl.pathname === '/' ? 'index.html' : parsedUrl.pathname);
    
    // Security check - prevent directory traversal
    if (!filePath.startsWith(path.resolve(__dirname))) {
        res.writeHead(403, { 'Content-Type': 'text/plain' });
        res.end('Forbidden');
        return;
    }
    
    serveFile(filePath, res);
});

server.listen(PORT, HOST, () => {
    console.log(`🌐 Frontend Development Server running at http://${HOST}:${PORT}/`);
    console.log(`📁 Serving files from: ${__dirname}`);
    console.log(`🔧 API Backend should be running at: http://localhost:8000`);
    console.log(`📚 API Documentation: http://localhost:8000/docs`);
    console.log(`\n🛑 Press Ctrl+C to stop the server`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down frontend server...');
    server.close(() => {
        console.log('✅ Frontend server stopped');
        process.exit(0);
    });
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Received SIGTERM, shutting down frontend server...');
    server.close(() => {
        console.log('✅ Frontend server stopped');
        process.exit(0);
    });
});