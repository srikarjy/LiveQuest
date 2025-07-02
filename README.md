# DeepPromptor Backend

A Node.js/Express backend service that integrates with Anthropic's Claude AI API to provide intelligent prompt generation and text processing capabilities.

## Features

- 🤖 **Claude AI Integration**: Powered by Anthropic's Claude Sonnet 4 model
- 🚀 **Express.js Server**: Fast and lightweight web server
- 🔐 **Environment Variables**: Secure API key management
- 📝 **JSON API**: RESTful endpoints for text generation
- 🔄 **Hot Reload**: Development server with nodemon
- ⚡ **CORS Enabled**: Cross-origin resource sharing support

## Prerequisites

Before running this project, make sure you have:

- **Node.js** (v14 or higher)
- **npm** or **yarn**
- **Anthropic API Key** (get one at [console.anthropic.com](https://console.anthropic.com))

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd deeppromptor
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   # Create .env file
   echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
   ```

   Replace `your-api-key-here` with your actual Anthropic API key that starts with `sk-ant-api03-`

## Usage

### Development Server

Start the development server with hot reload:

```bash
npm run dev
```

The server will start on `http://localhost:3000`

### Production Server

Start the production server:

```bash
npm start
```

## API Endpoints

### POST `/api/generate`

Generate AI-powered text based on input parameters.

**Request Body:**
```json
{
  "title": "Your Title Here",
  "selection": "demo"
}
```

**Response:**
```json
{
  "prompt": "Generated text response from Claude AI..."
}
```

**Example using curl:**
```bash
curl -X POST http://localhost:3000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Title","selection":"demo"}'
```

### GET `/health` (if implemented)

Check server health status.

**Response:**
```json
{
  "status": "OK",
  "timestamp": "2025-07-02T22:15:00.000Z"
}
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | ✅ |
| `PORT` | Server port (default: 3000) | ❌ |

### Model Configuration

The application currently uses:
- **Model**: `claude-sonnet-4-20250514` (Claude Sonnet 4)
- **Max Tokens**: 150
- **Temperature**: 0.7

You can modify these settings in `server.js`:

```js
const response = await anthropic.messages.create({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 150,
  temperature: 0.7,
  system: systemMessage,
  messages: messages
});
```

## Project Structure

```
deeppromptor/
├── server.js           # Main server file
├── package.json        # Dependencies and scripts
├── .env               # Environment variables (create this)
├── .gitignore         # Git ignore rules
├── README.md          # This file
└── node_modules/      # Dependencies (auto-generated)
```

## Dependencies

### Production Dependencies
- `@anthropic-ai/sdk`: Anthropic AI SDK for Claude integration
- `express`: Fast, unopinionated web framework
- `cors`: Enable Cross-Origin Resource Sharing
- `dotenv`: Load environment variables from .env file

### Development Dependencies
- `nodemon`: Monitor for changes and restart server automatically

## Error Handling

The API includes comprehensive error handling:

- **Authentication Errors**: Invalid API key
- **Model Errors**: Model not found or unavailable
- **Request Errors**: Malformed requests
- **Server Errors**: Internal server issues

All errors return appropriate HTTP status codes and descriptive error messages.

## Security

🔒 **Important Security Notes:**

1. **Never commit your `.env` file** - it's already in `.gitignore`
2. **Keep your API key secure** - don't share it publicly
3. **Use HTTPS in production** - encrypt all communications
4. **Validate input data** - sanitize user inputs

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Commit your changes: `git commit -m 'Add some feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## Troubleshooting

### Common Issues

**1. "Authentication Error" (401)**
- Check if your API key is correctly set in `.env`
- Ensure the API key starts with `sk-ant-api03-`

**2. "Model Not Found" (404)**
- Verify you're using the correct model name: `claude-sonnet-4-20250514`

**3. "Server won't start"**
- Check if port 3000 is already in use
- Ensure all dependencies are installed: `npm install`

**4. "Module not found"**
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

### Debugging

Enable detailed logging by checking your server console output. The application logs:
- API key status (first 8 characters)
- Request bodies
- Messages sent to Claude
- Full error details

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Review the [Anthropic API documentation](https://docs.anthropic.com)
3. Create an issue in this repository

## Changelog

### v0.1.0 (Current)
- Initial release
- Claude Sonnet 4 integration
- Basic Express.js server setup
- Environment variable configuration
- Error handling and logging 