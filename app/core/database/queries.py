INSERT_REDDIT_POST_UPDATE_TEMPLATE = """
        INSERT INTO {table_name} (
            post_id, title, username, created_utc, created_date, score,
            upvote_ratio, num_comments, permalink, user_url,
            subreddit, post_text, is_self, stickied, spoiler, locked,
            is_gallery, is_direct_image_post,
            flair_text, inline_images_in_text, markdown_image_urls,
            gallery_img_urls, image_post_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
         ON DUPLICATE KEY UPDATE
            title = VALUES(title),                  
            score = VALUES(score),                  
            upvote_ratio = VALUES(upvote_ratio),    
            num_comments = VALUES(num_comments),    
            post_text = VALUES(post_text),          
            stickied = VALUES(stickied),            
            spoiler = VALUES(spoiler),              
            locked = VALUES(locked),                
            flair_text = VALUES(flair_text),        
            inline_images_in_text = VALUES(inline_images_in_text), 
            markdown_image_urls = VALUES(markdown_image_urls),     
            is_gallery = VALUES(is_gallery),        
            is_direct_image_post = VALUES(is_direct_image_post),
            gallery_img_urls = VALUES(gallery_img_urls),
            image_post_url = VALUES(image_post_url)
        """

UPDATE_PORTFOLIO_STATUS_OF_POST_TEMPLATE = """
        UPDATE {table_name} SET
            processed = %s,
            is_portfolio = %s,
            failed = %s
        WHERE post_id = %s
        """

UPDATE_PORTFOLIO_TEMPLATE = """
        UPDATE {table_name} SET
            total_investment = %s,
            current_value = %s,
            profit_percentage = %s,
            profit_total = %s,
            btci_current_value = %s,
            btci_profit_percentage = %s,
            btci_profit_total = %s,
            updated_date = %s,
            btci_start_amount = %s
        WHERE source = %s AND source_id = %s
        """

INSERT_NEW_PORTFOLIO_TEMPLATE = """
        INSERT INTO {table_name} (
            source, source_id, total_investment, start_value,
            current_value, profit_percentage, profit_total,
            btci_current_value, btci_profit_percentage,
            btci_profit_total, created_date, updated_date,
            btci_start_amount
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            total_investment = VALUES(total_investment),
            start_value = VALUES(start_value),
            current_value = VALUES(current_value),
            profit_percentage = VALUES(profit_percentage),
            profit_total = VALUES(profit_total),
            btci_current_value = VALUES(btci_current_value),
            btci_profit_percentage = VALUES(btci_profit_percentage),
            btci_profit_total = VALUES(btci_profit_total),
            created_date = VALUES(created_date),
            updated_date = VALUES(updated_date),
            btci_start_amount = VALUES(btci_start_amount)
        """

INSERT_CRYPTO_CURRENCY_PRICE_TEMPLATE = """
        INSERT INTO {table_name} (
            name, abbreviation, price, currency, date, iso_week, iso_year
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            abbreviation = VALUES(abbreviation),
            price = VALUES(price),
            currency = VALUES(currency),
            date = VALUES(date),
            iso_week = VALUES(iso_week),
            iso_year = VALUES(iso_year)
        """

INSERT_NEW_PURCHASE_TEMPLATE = """
    INSERT INTO {table_name} (
        source, source_id, name, abbreviation, amount, purchase_price_per_unit,
        purchase_date, total_purchase_value
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        source = VALUES(source),
        source_id = VALUES(source_id),
        name = VALUES(name),
        abbreviation = VALUES(abbreviation),
        amount = VALUES(amount),
        purchase_price_per_unit = VALUES(purchase_price_per_unit),
        purchase_date = VALUES(purchase_date),
        total_purchase_value = VALUES(total_purchase_value)
"""

GET_PURCHASES_BY_SOURCE_ID_TEMPLATE = """
    SELECT * FROM {table_name}
    WHERE source = %s AND source_id = %s
    ORDER BY purchase_date ASC
"""

GET_PORTFOLIO_BY_SOURCE_ID_TEMPLATE = """
    SELECT * FROM {table_name}
    WHERE source = %s AND source_id = %s
    ORDER BY created_date DESC
"""
