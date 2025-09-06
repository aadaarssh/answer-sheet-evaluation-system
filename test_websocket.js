const WebSocket = require('ws');

// Test WebSocket connection
const ws = new WebSocket('ws://localhost:8000/api/ws');

ws.on('open', function open() {
    console.log('✅ WebSocket connection successful!');
    
    // Send a test message
    ws.send(JSON.stringify({
        type: 'ping',
        timestamp: Date.now()
    }));
});

ws.on('message', function message(data) {
    console.log('📨 Received:', JSON.parse(data.toString()));
    
    // Close after receiving response
    setTimeout(() => {
        ws.close();
    }, 1000);
});

ws.on('error', function error(err) {
    console.error('❌ WebSocket error:', err.message);
});

ws.on('close', function close() {
    console.log('🔌 WebSocket connection closed');
});

// Timeout if connection takes too long
setTimeout(() => {
    if (ws.readyState === WebSocket.CONNECTING) {
        console.error('❌ WebSocket connection timeout');
        ws.close();
    }
}, 5000);