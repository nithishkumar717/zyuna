const http = require('http');

// Lightweight HTTP Health Check endpoint for Cloud Hosting (Render, Koyeb, Railway)
const PORT = process.env.PORT || 8000;
http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ 
        status: 'online', 
        bot: 'Zyuna Music', 
        platform: 'Cloud', 
        timestamp: new Date().toISOString() 
    }));
}).listen(PORT, () => {
    console.log(`[Cloud-Health] HTTP Health Check listening on port ${PORT}`);
});

// Root entrypoint for Zyuna Music Bot
require('./Zyuna/index.js');

