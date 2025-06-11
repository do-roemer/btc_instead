INTERPRET_IMAGE_FROM_REDDIT_POST = \
    """"
    Look at this image coming from a crypto currency contet
    and describe what is shown on the picture.
    Watch out if there are any crypto currencies like
    Bitcoin(BTC), Ethereum(ETH), Solana(SOL) mentioned in
    the image with their amount and maybe the price and the
    price currency abbreviation (USD, EUR, CAD, etc.) and list them.



    Requirements! Provide your solution like the following:
    Decription: <description>
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
        <Crypto Currency name>|<Crypto Currency abbreviation>|<amount>|<price>|<price currency>
    In which:
        - <Crypto Currency name> is the name of the crypto currency
        - <Crypto Currency abbreviation> is the abbreviation of the crypto currency
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
            'positions':[
                {{
                    {{  'name': 'Crypto Currency name',
                        'abbreviation': abbreviation,
                        'amount': the shared amount,
                        'price': the shared price,
                        'currency': price currency 
                    }},
                    {{
                        'name': 'Crypto Currency name',
                        'abbreviation': abbreviation,
                        'amount': the shared amount,
                        'price': the shared price,
                        'currency': price currency
                    }}
                }}
            ]
        }}
    }}

    Here is the text:
    {vision_model_response}
    """
