---
title: ChatAgent BusinessInterior
emoji: 🏆
colorFrom: pink
colorTo: red
sdk: docker
app_port: 8000
pinned: false
---

# ChatAgent BusinessInterior

A FastAPI application for Business Interior chat agent that can be embedded in iframes.

## Embedding in an iframe

This application is configured to be embeddable in an iframe. You can embed it in your website using the following HTML:

```html
<iframe
  src="https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME"
  width="100%"
  height="800px"
  style="border: 1px solid #ddd; border-radius: 8px;"
  allow="camera;microphone"
></iframe>
```

Replace `YOUR_USERNAME` with your Hugging Face username and `YOUR_SPACE_NAME` with the name of your Space.

## API Documentation

The API documentation is available at `/docs` when the application is running.

## Local Development

1. Clone the repository
2. Install the dependencies: `pip install -r requirements.txt`
3. Run the application: `python app.py`

## Hugging Face Integration

This application uses Hugging Face's models for chat functionality. Make sure to set up the necessary environment variables for Hugging Face integration:

- `HF_TOKEN`: Your Hugging Face API token (optional)
- `HF_MODEL_NAME`: The name of the model to use (default: openai-community/gpt2)

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
