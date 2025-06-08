# Multi-Model LangGraph Research Agent

This project demonstrates a fullstack application using a React frontend and a LangGraph-powered backend agent with support for multiple AI models. The agent is designed to perform comprehensive research on a user's query by dynamically generating search terms, querying the web using Google Search, reflecting on the results to identify knowledge gaps, and iteratively refining its search until it can provide a well-supported answer with citations. This application serves as an example of building research-augmented conversational AI using LangGraph with support for Google Gemini, DeepSeek, GPT-4, and other models via OpenRouter.

![Gemini Fullstack LangGraph](./app.png)

## Features

- 💬 Fullstack application with a React frontend and LangGraph backend.
- 🧠 Powered by a LangGraph agent for advanced research and conversational AI.
- 🤖 **Multi-Model Support**: Choose between Google Gemini, DeepSeek R1, Qwen3, GPT-4.1, and more.
- 🔍 Dynamic search query generation using Google Gemini models.
- 🌐 Integrated web research via Google Search API.
- 🤔 Reflective reasoning to identify knowledge gaps and refine searches.
- 📄 Generates answers with citations from gathered sources.
- ⚙️ **Hybrid Architecture**: Fast Gemini models for search/web research, powerful models for reasoning/answers.
- 🎛️ **Configurable Research Depth**: Low, Medium, High effort levels.
- 🔄 Hot-reloading for both frontend and backend development during development.

## Supported AI Models

The application uses a **hybrid architecture** that automatically selects the optimal API for each task:

### **Available Models:**
- **Google Gemini 2.5 Pro Preview** - Advanced reasoning and comprehensive answers
- **DeepSeek R1** - State-of-the-art reasoning model with excellent performance
- **DeepSeek R1 Qwen3** - Lightweight version with good performance/cost ratio
- **Qwen3 235B** - Large-scale model for complex reasoning tasks
- **GPT-4.1** - OpenAI's latest model for high-quality responses

### **Hybrid Architecture:**
| **Task** | **API Used** | **Model** | **Reason** |
|----------|--------------|-----------|------------|
| Query Generation | Google Gemini | `gemini-2.0-flash` | Fast query optimization |
| Web Research | Google Gemini | `gemini-2.0-flash` | Native Google Search integration |
| Reflection & Analysis | User Selected | Any model above | Advanced reasoning where it matters |
| Final Answer | User Selected | Any model above | Best quality for final response |

This design ensures **optimal performance** and **cost efficiency** by using fast models for search tasks and powerful models for reasoning.

## Project Structure

The project is divided into two main directories:

-   `frontend/`: Contains the React application built with Vite.
-   `backend/`: Contains the LangGraph/FastAPI application, including the research agent logic.

## Getting Started: Development and Local Testing

Follow these steps to get the application running locally for development and testing.

**1. Prerequisites:**

-   Node.js and npm (or yarn/pnpm)
-   Python 3.8+
-   **API Keys**: The backend requires API keys for the AI models:
    
    **Required:**
    - **`GEMINI_API_KEY`**: Google Gemini API key (required for web search and query generation)
      - Get it from: https://ai.google.dev/
    
    **Optional (for additional models):**
    - **`OPENROUTER_API_KEY`**: OpenRouter API key (required for DeepSeek, GPT-4, Qwen3 models)
      - Get it from: https://openrouter.ai/keys
    
    **Setup:**
    1.  Navigate to the `backend/` directory.
    2.  Create a file named `.env` by copying the `backend/.env.example` file.
    3.  Open the `.env` file and add your API keys:
        ```env
        # Required - Google Gemini API Key
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
        
        # Optional - OpenRouter API Key (for DeepSeek, GPT-4, etc.)
        OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY"
        YOUR_SITE_URL="http://localhost:2024"
        YOUR_SITE_NAME="LangGraph Research Agent"
        ```

**2. Install Dependencies:**

**Backend:**

```bash
cd backend
pip install .
```

**Frontend:**

```bash
cd frontend
npm install
```

**3. Run Development Servers:**

**Backend & Frontend:**

```bash
make dev
```
This will run the backend and frontend development servers.    Open your browser and navigate to the frontend development server URL (e.g., `http://localhost:5173/app`).

_Alternatively, you can run the backend and frontend development servers separately. For the backend, open a terminal in the `backend/` directory and run `langgraph dev`. The backend API will be available at `http://127.0.0.1:2024`. It will also open a browser window to the LangGraph UI. For the frontend, open a terminal in the `frontend/` directory and run `npm run dev`. The frontend will be available at `http://localhost:5173`._

## How the Backend Agent Works (High-Level)

The core of the backend is a LangGraph agent defined in `backend/src/agent/graph.py`. It follows these steps using a **hybrid model approach**:

![Agent Flow](./agent.png)

1.  **Generate Initial Queries:** Based on your input, it generates a set of initial search queries using **Gemini 2.0 Flash** (optimized for speed).
2.  **Web Research:** For each query, it uses **Gemini 2.0 Flash with Google Search API** to find relevant web pages with grounding metadata and citations.
3.  **Reflection & Knowledge Gap Analysis:** The agent analyzes the search results using your **selected model** (Gemini, DeepSeek, GPT-4, etc.) to determine if information is sufficient or if there are knowledge gaps.
4.  **Iterative Refinement:** If gaps are found, it generates follow-up queries and repeats web research and reflection (up to configured maximum loops).
5.  **Finalize Answer:** Using your **selected model**, it synthesizes gathered information into a coherent answer with citations from web sources.

### **Why This Hybrid Approach?**
- ⚡ **Speed**: Gemini 2.0 Flash handles search tasks quickly
- 🔗 **Integration**: Native Google Search API integration with grounding metadata  
- 🧠 **Power**: Your chosen model (DeepSeek R1, GPT-4, etc.) handles complex reasoning
- 💰 **Cost-Effective**: Fast models for frequent operations, powerful models where quality matters

## Using the Application

### **Frontend Interface:**
1. **Model Selection**: Choose your preferred AI model from the dropdown (Gemini, DeepSeek R1, GPT-4.1, etc.)
2. **Research Effort**: Set the research depth:
   - **Low**: 1 query, 1 research loop (fastest)
   - **Medium**: 3 queries, 3 research loops (balanced)
   - **High**: 5 queries, 10 research loops (most thorough)
3. **Ask Questions**: Type your research question and watch the agent work
4. **Real-time Progress**: See live updates of the research process
5. **Cited Answers**: Get comprehensive answers with clickable source citations

### **Research Process Visualization:**
The interface shows real-time progress through:
- **🔍 Generating Search Queries** - Creating optimized search terms
- **🌐 Web Research** - Gathering information from multiple sources  
- **🤔 Reflection** - Analyzing if more information is needed
- **✨ Finalizing Answer** - Synthesizing the final response with citations

### **Model-Specific Behavior:**
- **Gemini Models**: Native integration, fastest performance
- **DeepSeek R1**: Advanced reasoning, excellent for complex queries
- **GPT-4.1**: High-quality responses, good for creative and analytical tasks
- **Qwen3**: Large-scale reasoning, good for research-heavy questions

### **Tips for Best Results:**
- Use **High effort** for complex research topics
- **DeepSeek R1** excels at analytical and reasoning tasks
- **Gemini 2.5 Pro** is great for balanced performance
- Ask follow-up questions to dive deeper into topics

## Deployment

In production, the backend server serves the optimized static frontend build. LangGraph requires a Redis instance and a Postgres database. Redis is used as a pub-sub broker to enable streaming real time output from background runs. Postgres is used to store assistants, threads, runs, persist thread state and long term memory, and to manage the state of the background task queue with 'exactly once' semantics. For more details on how to deploy the backend server, take a look at the [LangGraph Documentation](https://langchain-ai.github.io/langgraph/concepts/deployment_options/). Below is an example of how to build a Docker image that includes the optimized frontend build and the backend server and run it via `docker-compose`.

_Note: For the docker-compose.yml example you need a LangSmith API key, you can get one from [LangSmith](https://smith.langchain.com/settings)._

_Note: If you are not running the docker-compose.yml example or exposing the backend server to the public internet, you update the `apiUrl` in the `frontend/src/App.tsx` file your host. Currently the `apiUrl` is set to `http://localhost:8123` for docker-compose or `http://localhost:2024` for development._

**1. Build the Docker Image:**

   Run the following command from the **project root directory**:
   ```bash
   docker build -t gemini-fullstack-langgraph -f Dockerfile .
   ```
**2. Run the Production Server:**

   ```bash
   GEMINI_API_KEY=<your_gemini_api_key> \
   OPENROUTER_API_KEY=<your_openrouter_api_key> \
   LANGSMITH_API_KEY=<your_langsmith_api_key> \
   docker-compose up
   ```
   
   **Note**: `OPENROUTER_API_KEY` is optional - without it, only Gemini models will be available.

Open your browser and navigate to `http://localhost:8123/app/` to see the application. The API will be available at `http://localhost:8123`.

## Technologies Used

### **Frontend:**
- [React](https://reactjs.org/) (with [Vite](https://vitejs.dev/)) - For the frontend user interface.
- [Tailwind CSS](https://tailwindcss.com/) - For styling.
- [Shadcn UI](https://ui.shadcn.com/) - For components.

### **Backend:**
- [LangGraph](https://github.com/langchain-ai/langgraph) - For building the backend research agent.
- [Google Gemini](https://ai.google.dev/models/gemini) - LLM for query generation and web research.
- [OpenRouter](https://openrouter.ai/) - API gateway for accessing multiple AI models (DeepSeek, GPT-4, Qwen3).

### **AI Models:**
- **Google Gemini 2.0 Flash** - Fast query generation and web search
- **Google Gemini 2.5 Pro** - Advanced reasoning and answers  
- **DeepSeek R1** - State-of-the-art reasoning model
- **GPT-4.1** - OpenAI's latest model
- **Qwen3 235B** - Large-scale reasoning model

## Troubleshooting

### **Common Issues:**

**"OpenRouter models not working"**
- Ensure `OPENROUTER_API_KEY` is set in your `.env` file
- Get your key from: https://openrouter.ai/keys
- The app will warn you if the key is missing

**"No citations/sources in answers"**
- This is expected for OpenRouter models - citations come from Google Search integration
- Final answers will include a **Sources** section with relevant links
- Gemini models have the best citation integration

**"Processing screen stuck"**
- Check console logs for API errors
- Verify both `GEMINI_API_KEY` and `OPENROUTER_API_KEY` are valid
- Ensure you have sufficient API credits

**"Models missing in dropdown"**  
- Only Gemini models will show if `OPENROUTER_API_KEY` is not configured
- This is normal and expected

### **Performance Notes:**
- **Gemini models**: Fastest performance, best integration
- **DeepSeek R1**: Excellent quality/price ratio  
- **GPT-4.1**: Highest quality but slower and more expensive
- **High effort mode**: Can take 2-5 minutes for complex queries

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details. 