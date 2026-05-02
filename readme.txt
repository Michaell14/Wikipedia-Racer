Project Name: Wikipedia Racer

Project Description:
Wikipedia Racer is a web game where you race against an AI bot to get from one random Wikipedia page to another. You have to find the shortest path using only the links on each page. The backend scrapes live data from Wikipedia and caches the links to build a directed graph of articles. While the player is clicking through pages, the bot uses a graph traversal algorithm and NLP embeddings to figure out which links are most relevant to the target topic. We built this to show how complex information networks like the web can be navigated efficiently using basic search algorithms and semantic analysis.

Categories Used:
- Graph and Graph Algorithms: We modeled Wikipedia as a massive graph where articles are nodes and links are edges. The bot uses a Best-First Search approach with a priority queue to find its way through the network.
- Information Networks: The project is built directly around the structure of the World Wide Web. We scrape real-world data from Wikipedia to create a playable information network.
- Document Search (Information Retrieval): The bot decides its next move by ranking the available links based on their semantic similarity to the goal. This is essentially a small-scale information retrieval system using text embeddings.

Work Breakdown:
- Michael: Handled the frontend architecture, building the interactive React user interface to display the dual view of the Wikipedia iframe and the live bot activity log. Also implemented the WebSocket client for real-time race synchronization.
- Evan: Designed the core backend infrastructure using FastAPI and SQLAlchemy. Developed the web scraping and caching logic to fetch and store Wikipedia articles, ensuring the game runs smoothly without overloading the Wikipedia API.
- Lucas: Developed the bot engine and graph traversal logic. Implemented the embedding service to calculate text similarities and integrated the priority queue system to guide the bot's decision-making process through the information network.

AI/LLM Usage:
We used AI tools in a limited capacity for this project. The main use case was using ChatGPT and Claude to help with the CSS and styling of the website, especially for getting the layout to look right with Tailwind and shadcn/ui. We also used LLMs to help debug some of the more confusing parts of the FastAPI WebSocket documentation. All of the core game logic, the bot's traversal algorithm, and the overall system architecture were designed and implemented by our team.

Changes Since Last Proposal:
We didn't make any major changes to the scope. The final project matches what we originally planned, though we spent a bit more time on the UI polish than we initially expected.
