# 🔑 API Key Setup

To use the A2A Demo system, you need to set up your OpenAI API key.

## Quick Setup

1. **Get your OpenAI API key** from [OpenAI Platform](https://platform.openai.com/api-keys)

2. **Add it to the environment file**:
   ```bash
   echo "OPENAI_API_KEY=your_actual_api_key_here" > .env
   ```

3. **Replace `your_actual_api_key_here` with your real API key**

## What uses the API key?

- ✅ **Frontend (Next.js)**: Automatically loads from `.env`
- ✅ **Finance Agent**: Loads from `../.env` 
- ✅ **IT Agent**: Loads from `../.env`
- ✅ **Buildings Agent**: Loads from `../.env`
- ✅ **Agno AGI Agent**: Loads from `../.env`

## Verify Setup

Run the system and check that you don't see API key errors:
```bash
./run_agents.sh
```

In another terminal:
```bash
npm run dev
```

All agents and the frontend will now use the same centralized API key! 🎉
