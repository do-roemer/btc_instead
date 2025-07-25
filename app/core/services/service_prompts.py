INTERPRET_IMAGE_FROM_REDDIT_POST = \
    """"
    You are an expert in extracting Crypto Currency information from images.

    Your goal is to extract all price relevant information about
    crypto currencies like Bitcoin(BTC), Ethereum(ETH),
    Solana(SOL) from the image and list them. Relevant information is their
    amount and maybe the price and the price currency abbreviation
    (USD, EUR, CAD, etc.).

    Follow these steps:
    1. Describe what you see in the image.
    2. Identify the crypto currencies mentioned in the image.
    3. Identify the amount of each crypto currency and additional information
    related to the currency.
    4. Write your findings from step 1 to 3 into description in the output.
    5. Provide the list of crypto currencies in the required format.

    Requirements:
    1. Ensure that you covered all mentioned crypto currencies. Even if
    you might know the crypto currency, you have to extract it from the image.
    2. Provide your solution like in the following pattern:
    Description: <description>
    List of Crypto Currencies:
    - <Crypto Currency name>|<Crypto Currency abbreviation>|<amount>|<price>|<price currency>
    - <Crypto Currency name>|<Crypto Currency abbreviation>|<amount>|<price>|<price currency>
    - <Crypto Currency name>|<Crypto Currency abbreviation>|<amount>|<price>|<price currency>
    """

IMAGE_PORTFOLIO_REASONING_PROMPT = \
    """
    ## Instructions
    You are an expert in Crypto Currencies and you are able to
    identify if the provided information is describing a Crypto Portfolio
    or not. You are also able to identify the shared crypto currencies
    and their amount and price and process them into a standardized format.

    ## Input
    You get a decription of an image from a Crypto Currencies context and
    a list of crypto currencies and their amount and maybe their value which
    where also present in the image.
    Your task is now to decide from the provided input if it is
    describing a Crypto Portfolio and the possible shared list of crypto
    currencies are the holdings of that portfolio.
    The information of each element of the list is structured like this:
        <crypto currency name>|<crypto currency abbreviation>|<amount>|<price>|<price currency>
    In which:
        - <crypto currency name> is the name of the crypto currency
        - <crypto currency abbreviation> is the abbreviation of the crypto currency
        - <amount> is the amount of the crypto currency
        - <price> is the price of the crypto currency in float number
        - <price currency> is the currency of the price like USD, EUR, CAD, etc.

    ## Requirements for the output
        - The price needs to be a float number without any currency symbol like $, €, etc.
        - The amount has to be a float number and if Metric Prefix Notation is used, it has to be converted to a float number.
          like 1.5k has to be converted to 1500.0 
        
    
    Provide the output as JSON and ensure the output is ONLY the JSON
    object, without any introductory text or code fences.
    {{
        {{
            'is_portfolio': True or False
        }},
        {{
            'purchases':[
                {{
                    {{  'name': <crypto currency name>,
                        'abbreviation': <crypto currency abbreviation>,
                        'amount': <amount>,
                        'price': <price>,
                        'currency': <price currency>
                    }},
                    {{
                        'name': <crypto currency name>,
                        'abbreviation': <crypto currency abbreviation>,
                        'amount': <amount>,
                        'price': <price>,
                        'currency': <price currency>
                    }}
                }}
            ]
        }}
    }}

    Here is the text:
    {vision_model_response}
    """
