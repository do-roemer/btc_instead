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

UPDATE_PORTFOLIO_STATUS_OF_POST = """
        UPDATE {table_name} SET
            processed = %s,
            is_portfolio = %s,
            failed = %s
        WHERE post_id = %s
        """

INSERT_NEW_PORTFOLIO_TEMPLATE = """
        INSERT INTO {table_name} (
            source, source_id, total_investment, start_value,
            current_value, profit_percentage, profit_total,
            btci_current_value, btci_profit_percentage,
            btci_profit_total, created_date, updated_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s)
        ON DUPLICATE KEY UPDATE
            total_investment = VALUES(total_investment),
            start_value = VALUES(start_value),
            current_value = VALUES(current_value),
            profit_percentage = VALUES(profit_percentage),
            profit_total = VALUES(profit_total),
            btci_current_value = VALUES(btci_current_value),
            btci_profit_percentage = VALUES(btci_profit_percentage),
            btci_profit_total = VALUES(btci_profit_total),
            updated_date = VALUES(updated_date)
        """

INSERT_CRYPTO_CURRENCY_PRICE_TEMPLATE = """
        INSERT INTO {table_name} (
            abbreviation, price, date
        ) VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            abbreviation = VALUES(abbreviation),
            price = VALUES(price),
            date = VALUES(date)
        """
