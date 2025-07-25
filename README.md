# BTC Instead

> [A "told you so!" project to compare what would have happend if bitcoin was bought instead of altcoins.]

<!-- BADGES -->
<div align="center">
  <a href="https://github.com/do-roemer/btc_instead/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/do-roemer/btc_instead.svg?style=for-the-badge" alt="Contributors">
  </a>
  <a href="https://github.com/do-roemer/btc_instead/stargazers">
    <img src="https://img.shields.io/github/stars/do-roemer/btc_instead.svg?style=for-the-badge" alt="Stargazers">
  </a>
  <a href="https://github.com/do-roemer/btc_instead/issues">
    <img src="https://img.shields.io/github/issues/do-roemer/btc_instead.svg?style=for-the-badge" alt="Issues">
  </a>
  <a href="https://github.com/do-roemer/btc_instead/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/do-roemer/btc_instead.svg?style=for-the-badge" alt="License">
  </a>
</div>

---

## Table of Contents

- [About The Project](#about-the-project)
  - [Built With](#built-with)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Acknowledgments](#acknowledgments)

---

## About The Project
This is a personal project to improve my skills in planing, outlining, developing and deploying a project. The topic is secondary and I mainly want 
to enhance my skills in deploying apps in docker, providing APIs, use GenAI in a live environment, etc.

**BTC Instead** is (will be) a [web app] that takes (crypto) portfolios shared on subreddits and makes the comparison if the person would have just BTC instead.

I'm interested in Bitcoin and Bitcoin only and for me Crypto (all the other coins) and Bitcoin are two different things. When I scroll through reddit I see so much scam and hope of getting rich soon by just buying tokens from a bunch of non-sense projects where only the owners of the project will benefit from. I tend to go into discussions and that's where I came up with the idea of just letting the people know how their portfolio would look like today, if they bought **Bitcoin instead**.

I use the Google Gemini LLM and ProVision model to process images posted on reddit. Basically, I let the vision model get the text out of the image and let it decide if it is a portfolio or not. If yes, the LLM takes the text and pus it into a JSON format to be further processed by the application.
In the uture I would also liek to use the LLM to interpret the sentiment of comments and get more stats.

But again, this is my personal project and point of view and I put my freetime into this project bcs. I want to learn something.  


### Built With
This project was built with the following technologies:

*   **Backend:**
    *   Python
    *   SQL
    *   Google Gemini
    *   Docker
*   **Data Source:**
    *   [Reddit](https://www.reddit.com/)
    *   [Coingecko](https://www.coingecko.com/en/api)
    *   [Coin Market Cap](https://coinmarketcap.com/)
*   **Deployment:**
    *   [Docker](https://www.docker.com/)
    *   [DigitalOcean](https://www.digitalocean.com/?utm_medium=affiliates&utm_source=impact&utm_campaign=5843390&utm_content=&irgwc=1&irclickid=26qU8X2M3xycUKKQFXWM90G3UksR9myKHS-MSA0&gad_source=1&gad_campaignid=21599698028&gbraid=0AAAAA9nmATaLXItjrn6VOE-5tHVqB6d9s&gclid=Cj0KCQjwxo_CBhDbARIsADWpDH4-WlE2SLXl7F8N4tatOB1JLCnyI6nOvNTOZGCQbvhIl1WnTGcpkQoaAlWUEALw_wcB)

## Roadmap

- [x] Fetch data from Subreddit and store it in MySQL DB
- [x] Use Google Pro Vision and Gemini LLM to extract assets out of reddit posts and images
- [x] Inital API endpoint to add reddit posts to the DB
- [x] An API endpoint that takes an URL and triggers the whole reddit post process and portfolio evaluation
- [x] Create portfolios, connect it with the extracted assets and save it in DB
- [x] Add logic to compare the actual portfolio with the performance of a BTC only portfolio
- [ ]  A simple frontend/dashboard to show the portfolios and their stats on a website

- [x] Setup a server on a DigitalOcean droplet to run run the following services:
  - [x]  MySQl DB via Docker image and accessable via ssh tunel
  - [x]  Run the Reddit fetcher script on a daily base
  - [ ]  Deploy API endpoints on a server and make them accessible

See the [open issues](https://github.com/[YOUR_USERNAME]/btc_instead/issues) for a full list of proposed features (and known issues).

---

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

## Contact

Dominik Römer  - [dom.roemer.92@gmail.com](mailto:dom.roemer.92@gmail.com)

Project Link: [https://github.com/do-roemer/btc_instead](https://github.com/do-roemer/btc_instead)

---

## Acknowledgments

A big thank you to the following resources that made this project possible:
*   [CoinGecko API](https://www.coingecko.com/en/api)
*   [Coin Market Cap API](https://coinmarketcap.com/api/)

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
