# TwitterNewsCarros

This repository contains a bot that publishes news about car prices and the automotive industry in Mexico on Twitter. The bot uses the Perplexity API to search for relevant articles and generates concise tweets summarizing the key points.

## Features
- **News Sources**: The bot fetches news from a curated list of Mexican websites focused on the automotive industry.
- **Search Queries**: The bot uses predefined search terms to find the most relevant articles about car prices, market trends, and industry updates.
- **Automated Posting**: Tweets are generated and posted automatically at scheduled intervals.
- **History Management**: Keeps track of posted articles to avoid duplicates.

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/TwitterNewsCarros.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables or a `config.toml` file with the following keys:
   - `PERPLEXITY_API_KEY`
   - `TWITTER_API_KEY`
   - `TWITTER_API_SECRET`
   - `TWITTER_ACCESS_TOKEN`
   - `TWITTER_ACCESS_TOKEN_SECRET`

## Usage
Run the bot locally:
```bash
python main.py
```

## Contributing
Feel free to submit issues or pull requests to improve the bot.

## License
This project is licensed under the MIT License.