import time
from chunk_selection import get_project_context
from llm_connection import get_openai_completion


token_prompt = 'You are a helpful assistant. brief and precise. You are extracting information from scrapped crypto project websites.\n' \
               'Extract the name of the token and token symbol!\n' \
               'If no token or token symbol mentioned in the text then answer: No information found!\n' \
               'Answer format:\n' \
               'token name, token symbol'


def extract_token_info(text_chunks, embeddings, logger, max_retries=3):
    project_context = get_project_context(text_chunks, embeddings, prompt=token_prompt, top_k=10)
    logger.info(f'chain extraction context: {project_context}')

    retries = 0
    while retries < max_retries:
        response = get_openai_completion(token_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            return response
    return 'Extraction failed.'

chain_prompt = 'You are a helpful assistant. brief and precise. You are extracting information from scrapped crypto project websites.\n' \
               'Extract which chains the project available or planning to be deployed!\n' \
               'If no chain mentioned in the text then answer: No chain information found!'


def extract_chain_info(text_chunks, embeddings, logger, max_retries=3):
    project_context = get_project_context(text_chunks, embeddings, prompt=chain_prompt, top_k=10)
    #logger.info(f'chain extraction context: {project_context}')

    retries = 0
    while retries < max_retries:
        response = get_openai_completion(chain_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            return response
    return 'Extraction failed.'


area_prompt = 'You are a helpful assistant. brief and precise. You are extracting information from scrapped crypto project websites.\n' \
              'Assign the project to an area based on the available texts! Answer the name of the area only!\n\nAreas:\n' \
              "Decentralized Financial Infrastructure" \
              "Decentralized Exchanges (DEXs)" \
              "Decentralized Lending and Borrowing Protocols" \
              "Yield Farming and Liquidity Mining Mechanisms" \
              "Decentralized Asset Management Solutions" \
              "Decentralized Derivatives Trading Platforms" \
              "Play-to-Earn (P2E) Gaming Ecosystems" \
              "Non-Fungible Token (NFT) Integration in Games" \
              "Metaverse-based Gaming Experiences" \
              "Gaming Guilds and Infrastructure" \
              "Blockchain-powered GameFi Marketplaces" \
              "NFT Collectibles and Digital Assets" \
              "NFT Marketplaces and Trading Platforms" \
              "Fractionalized NFT Ownership and Fractionalization" \
              "NFT Applications in Gaming, Art, and Collectibles" \
              "NFT-powered Metaverse Experiences" \
              "Cryptocurrency Exchanges and Custodial Wallets" \
              "Centralized Lending and Borrowing Platforms" \
              "Institutional Adoption of Cryptocurrency" \
              "Regulated CeFi Products and Services" \
              "Virtual Worlds and Decentralized Platforms" \
              "Metaverse Avatars, Fashion, and Digital Goods" \
              "Metaverse Land and Real Estate Ownership" \
              "Metaverse Infrastructure and Protocol Development" \
              "Social Experiences and Communities in the Metaverse" \
              "Governance DAOs for Protocol Management" \
              "Investment DAOs for Asset Management" \
              "Social DAOs for Community Building" \
              "Protocol DAOs for Decentralized Applications" \
              "Infrastructure DAOs for Ecosystem Support" \
              "Scalable and Secure Blockchain Protocols" \
              "Layer 1 and Layer 2 Blockchain Solutions" \
              "Consensus Mechanisms and Blockchain Security" \
              "Blockchain Interoperability and Cross-Chain Bridges" \
              "Blockchain Privacy and Zero-Knowledge Proofs (ZKPs)" \
              "Fiat-backed, Crypto-backed, and Algorithmic Stablecoins" \
              "Stablecoin Exchanges and Payment Gateways" \
              "Stablecoin Integration in DeFi and CeFi Applications" \
              "Regulatory Landscape and Governance of Stablecoins" \
              "Stablecoin Adoption and Impact on Financial Markets" \
              "Retail CBDC Design and Implementation" \
              "Wholesale CBDC Exploration and Pilot Projects" \
              "CBDC Regulation, Governance, and Cross-border Interoperability" \
              "CBDC Impact on Financial Systems and Monetary Policy" \
              "CBDC Adoption and Usage Scenarios" \
              "Privacy-enhancing Technologies and Zero-Knowledge Proofs (ZKPs)" \
              "Anonymous Cryptocurrencies and Mixers" \
              "Privacy Coin Regulations and Regulatory Compliance" \
              "Privacy Coin Adoption and Use Cases" \
              "Privacy-preserving Blockchain Protocols and Applications" \
              "Security Token Offerings (STOs) and Asset Tokenization" \
              "Real Estate Tokenization and Fractional Ownership" \
              "Art and Collectibles Tokenization" \
              "Tokenized Commodities and Asset Backed Coins" \
              "Tokenized Securities and Equity Representation" \
              "Oracle Services and Secure Data Feeds" \
              "Decentralized Identity (DID) Solutions and Self-sovereign Identity" \
              "Data Ownership and Privacy Protection Frameworks" \
              "Decentralized Social Networking and Social Media Platforms" \
              "RegTech (Regulatory Technology) for Blockchain Compliance" \
              "AI and Machine Learning Applications in Blockchain" \
              "Blockchain-powered Sustainable Energy Solutions" \
              "Supply Chain Traceability and Optimization via Blockchain" \
              "Blockchain for Secure and Efficient Healthcare Data Management" \
              "Blockchain-based Educational Records and Credentials" \
              "Social Tokens and Influencer Engagement on Blockchain" \
              "Blockchain-powered Insurance Protocols" \
              "Esports and Online Gaming Integration with Blockchain" \
              "Blockchain-based Agricultural Supply Chain Management" \
              "Secure and Efficient Crypto Hardware Wallets" \
              "Crypto Tax and Accounting Solutions and Regulations" \
              "Quantum-resistant Cryptography and Blockchain Security" \
              "Blockchain for Industry 4.0 and Manufacturing Automation" \
              "Blockchain-enabled Tourism and Travel Experiences" \
              "Cryptocurrency Legal Services and Regulatory Guidance" \
              "Blockchain-powered Media and Entertainment Distribution" \
              "Blockchain for Retail and eCommerce Supply Chain Management" \
              "Blockchain-based Energy Trading and Market" \
              "Cross-Chain and Multi-Chain Solutions" \
              "Smart Contract Development and Auditing" \
              "Crypto Analytics and Market Intelligence" \
              "Decentralized Autonomous Corporations (DACs)" \
              "Blockchain in IoT (Internet of Things)" \
              "Crypto Philanthropy and Charitable Giving" \
              "Blockchain in Digital Identity and KYC (Know Your Customer)" \
              "Blockchain in Government and Public Services" \
              "Interplanetary File System (IPFS) and Decentralized Storage Solutions" \
              "Crypto-friendly Banking Services" \
              "Layer 3 Solutions" \
              "Blockchain in Digital Rights Management" \
              "Decentralized Web Services (Web3)" \
              "Quantum Computing and Blockchain"


def extract_area_info(text_chunks, embeddings, logger, max_retries=3):
    project_context = get_project_context(text_chunks, embeddings, prompt=area_prompt, top_k=10)
    #logger.info(f'chain extraction context: {project_context}')

    retries = 0
    while retries < max_retries:
        response = get_openai_completion(area_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            return response
    return 'Extraction failed.'
