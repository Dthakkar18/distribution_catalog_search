from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import os
import time

# Load environment variables from the .env file
load_dotenv()

# Set Chrome options
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

# Set up ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the login page
driver.get("https://app.ghst.io/auth/sign-in")  # Sign in URL

# Allow the page to load
time.sleep(2)

# Find and fill in sign in details
username_field = driver.find_element(By.NAME, "email")  # The element name/id for email
password_field = driver.find_element(By.NAME, "password")  # The element name/id for password
username_field.send_keys(os.getenv("GHOST_DIST_EMAIL"))  
password_field.send_keys(os.getenv("GHOST_DIST_PASS"))

# Click the sign in button
login_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="button-submitNext"]')
login_button.click()

# Wait for sign in to complete
time.sleep(5)

# Go to the amazon products catalog URL 
driver.get("https://app.ghst.io/collection/new?listings_v1%5BrefinementList%5D%5BmarketplaceSources%5D%5B0%5D=Amazon")

# Find the number of listings in <p> tag
wait = WebDriverWait(driver, 10)
p_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.MuiTypography-root.MuiTypography-bodyLargeLight.mui-1j520so')))

# Get the page source after the <p> tag element has loaded
page_source = driver.page_source

# Parse the page source with BeautifulSoup
soup = BeautifulSoup(page_source, 'html.parser')

# Find the <p> tags by their class and extract the text
p_tags = soup.find_all('p', class_='MuiTypography-root MuiTypography-bodyLargeLight mui-1j520so')
# The last <p> has the content we need (number of listings)
last_p_tag = p_tags[-1].text.strip() # Content of tag
number_of_listings = last_p_tag.split(" ")[0] # Just get the number

print(f'The number of listings are: {number_of_listings}')


# Get all hrefs for all the listings
hrefs = set()
while True:
    try:
        # Wait until at least one button is present
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button.MuiButtonBase-root')))

        # Find all buttons matching the selector
        buttons = driver.find_elements(By.CSS_SELECTOR, 'button.MuiButtonBase-root')

        load_more_button = None
        for button in buttons:
            if button.text.strip() == "Load More":  # Ensure exact text match
                print('Found "Load More" button')
                load_more_button = button
                break  # Get only the first matching button

        if not load_more_button:
            print("No more 'Load More' button, exiting loop.")
            break  # Exit loop when the button disappears

        # Ensure the button is clickable before clicking
        wait.until(EC.element_to_be_clickable(load_more_button))
        load_more_button.click()

        # Wait for new content to load
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.MuiGrid2-root.MuiGrid2-container.MuiGrid2-direction-xs-row.mui-1mtmhly')))

        # Get updated page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract all hrefs from the dynamically loaded divs
        child_divs = soup.select('.MuiGrid2-root.MuiGrid2-container.MuiGrid2-direction-xs-row.mui-1mtmhly div a')
        for a_tag in child_divs:
            href = a_tag.get('href')
            if href:
                hrefs.add(href)  # Using a set to avoid duplicates

    except Exception as e:
        print(f"Error occurred: {e}")
        break  # Exit loop in case of an unexpected error

# Final scrape to ensure that the last href is captured
page_source = driver.page_source
soup = BeautifulSoup(page_source, 'html.parser')

# Extract all hrefs from the final page load
child_divs = soup.select('.MuiGrid2-root.MuiGrid2-container.MuiGrid2-direction-xs-row.mui-1mtmhly div a')
for a_tag in child_divs:
    href = a_tag.get('href')
    if href:
        hrefs.add(href)  # Using a set to avoid duplicates

# Convert set to list (if needed)
hrefs_list = list(hrefs)

# Optionally, print all hrefs at the end
# print("Total hrefs:", len(hrefs_list))
# for i in hrefs_list: print(i)

# Next steps:
# - got to all url with href and bottom query in url and then get asin, sales per month, etc and sotre asins in list
# - query for each listing href ?products_v1_ungrouped_units_desc%5BrefinementList%5D%5BmarketplaceSources%5D%5B0%5D=Amazon


input("Press Enter to close the browser...")
driver.quit()
