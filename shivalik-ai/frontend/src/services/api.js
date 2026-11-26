
const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ||
    "http://127.0.0.1:8000";

export async function sendChatMessage(
    question,
    signal,
    conversationId = null
) {
    const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            question,
            conversation_id: conversationId,
        }),
        signal,
    });

    if (!response.ok) {
        let detail = `Chat request failed with status ${response.status}`;

        try {
            const errorData = await response.json();
            detail = errorData.detail || detail;
        } catch {
            // Keep the default error message.
        }

        const error = new Error(detail);
        error.status = response.status;
        throw error;
    }

    return response.json();
}
