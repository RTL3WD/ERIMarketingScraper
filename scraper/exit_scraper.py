def exit_scraper(driver,df=None):
    """Exit the scraper."""
    try:
        if df is not df.empty:
            df.to_csv("scrape-results.csv",index=False)
    finally:
        driver.quit()
        print("Exiting the scraper from exit scraper function...")