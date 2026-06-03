from flask import Flask, request, jsonify, Response
import json
import uuid
from datetime import datetime

app = Flask(__name__)

# Task storage (use database in production)
tasks = {}

@app.route('/.well-known/agent.json')
def agent_card():
    """Serve the Agent Card for discovery."""
    return jsonify({
        "name": "DataAnalysisAgent",
        "description": "Analyzes datasets and generates insights",
        "url": "https://agents.example.com",
        "skills": [
            {
                "id": "analyze-csv",
                "name": "CSV Analysis",
                "description": "Analyze CSV files and generate statistical insights"
            }
        ]
    })

@app.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task (A2A task creation endpoint)."""
    data = request.json

    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "status": "pending",
        "skill": data.get("skill"),
        "input": data.get("input"),
        "createdAt": datetime.utcnow().isoformat(),
        "messages": [],
        "artifacts": []
    }

    tasks[task_id] = task

    # In production, queue task for async processing
    process_task_async(task_id)

    return jsonify({
        "id": task_id,
        "status": "pending",
        "statusMessage": "Task queued for processing"
    }), 202

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """Get task status and results."""
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({
        "id": task["id"],
        "status": task["status"],
        "messages": task["messages"],
        "artifacts": task["artifacts"]
    })

@app.route('/tasks/<task_id>/messages', methods=['POST'])
def add_message(task_id):
    """Send a message to an ongoing task (collaboration)."""
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    message = request.json
    message["timestamp"] = datetime.utcnow().isoformat()
    task["messages"].append(message)

    return jsonify({"status": "message received"})

@app.route('/tasks/<task_id>/stream')
def stream_task(task_id):
    """Stream task progress via SSE."""
    def generate():
        task = tasks.get(task_id)
        if not task:
            yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
            return

        # Simulate streaming progress
        yield f"data: {json.dumps({'status': 'in_progress', 'progress': 0})}\n\n"

        # In production, yield actual progress updates
        for progress in [25, 50, 75, 100]:
            yield f"data: {json.dumps({'status': 'in_progress', 'progress': progress})}\n\n"

        yield f"data: {json.dumps({'status': 'completed', 'result': task.get('result')})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

def process_task_async(task_id):
    """Process task asynchronously (simplified)."""
    task = tasks[task_id]
    task["status"] = "in_progress"

    # Simulate processing
    task["result"] = {
        "insights": ["Insight 1", "Insight 2"],
        "summary": "Analysis complete"
    }
    task["status"] = "completed"

if __name__ = '__main__':
    app.run(port80)