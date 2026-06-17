# This is actually JavaScript/TypeScript but shown for reference
# In a Python context, this would be the client-side code

"""
// Browser-side streaming client implementation

async function streamChat(prompt) {
    const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullText = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                if (data.text) {
                    fullText += data.text;
                    updateUI(fullText);  // Update display progressively
                }
                if (data.done) {
                    return fullText;
                }
            }
        }
    }
    return fullText;
}

// WebSocket alternative
function connectWebSocket(onMessage) {
    const ws = new WebSocket('wss://api.example.com/ws');

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type == 'content') {
            onMessage(data.text);
        } else if (data.type == 'complete') {
            ws.close();
        }
    };

    return ws;
}
"""