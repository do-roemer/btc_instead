from server_scripts.fetch_weekly_cc_prices import pipeline as weekly_prices_pipeline

if __name__ == "__main__":
    print("Executing daily pipeline from top-level entry point...")
    weekly_prices_pipeline()
    print("Pipeline execution finished.")