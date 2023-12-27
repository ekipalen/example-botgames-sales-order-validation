import time
from robocorp import browser, log
from pathlib import Path
from robocorp.tasks import get_output_dir, task

OUTPUT_DIR = get_output_dir() or Path("output")
CSV_PATH = OUTPUT_DIR / "Sales Order.csv"
CHALLENGE_URL = "https://developer.automationanywhere.com/challenges/salesorder-challenge.html"
SALES_APP_URL = "https://developer.automationanywhere.com/challenges/salesorder-applogin.html"
TRACKING_URL = "https://developer.automationanywhere.com/challenges/salesorder-tracking.html"
USERNAME = "douglasmcgee@catchycomponents.com"
PASSWORD = "i7D32S&37K*W"

@task
def solve_the_botgames_challenge():
    """ Complete the Sales Order Validation challenge. """
    launch_browser()
    open_challenge_page()
    open_tracking_page()
    open_sales_app_and_login()
    validate_the_orders("Confirmed")
    validate_the_orders("Delivery Outstanding")
    download_csv()
    collect_the_results()

def launch_browser():
    browser.configure(
        browser_engine="chromium",
        screenshot="only-on-failure",
        headless=False,
    )
    # user_agent is needed for headless runs
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    context = browser.context()
    context.set_extra_http_headers({"User-Agent": user_agent})

def open_challenge_page():
    """ Open the challenge page and accept the cookies. """
    browser.goto(CHALLENGE_URL)
    global challenge_page
    challenge_page = browser.page()
    challenge_page.click("#onetrust-accept-btn-handler", no_wait_after=True)

def open_tracking_page():
    """ Open the Tracking application into a separate browser tab. """
    global tracking_page
    tracking_page = browser.context().new_page()
    tracking_page.goto(TRACKING_URL)

def open_sales_app_and_login():
    """ Open the Sales application into a separate tab and login. """
    global sales_app_page
    sales_app_page = browser.context().new_page()
    sales_app_page.goto(SALES_APP_URL)
    sales_app_page.fill("//input[@id='salesOrderInputEmail']", USERNAME)
    sales_app_page.fill("//input[@id='salesOrderInputPassword']", PASSWORD)
    sales_app_page.click("//a[contains(text(),'Login')]")
    sales_app_page.click("//span[contains(text(),'Sales Order')]")
    sales_app_page.select_option("select[name='salesOrderDataTable_length']", "100") 

def validate_the_orders(search_phrase): 
    """ 
    Perform a search using the search phrase from input argument. 
    Iterate through the order details and validate the status of each products in orders. 
    If the order has been delivered, click "Generate Invoice", else just minimize the order.  
    """
    sales_app_page.fill("//input[@type='search']",search_phrase)
    number_of_orders = sales_app_page.query_selector_all(("//td[contains(text(),'SO-')]"))
    row_counter = 1
    for item in range (0, len(number_of_orders)):
        sales_app_page.click(f"//tbody/tr[{row_counter}]/td[1]")
        orders = sales_app_page.query_selector_all("//td[contains(text(),'TR-')]")
        result = search_for_orders(orders)
        if result == "Delivered":
            sales_app_page.click("//button[contains(text(),'Generate Invoice')]")
        else: 
            sales_app_page.click("//i[contains(@class, 'minus')]")
            row_counter += 1

def search_for_orders(orders):
    """ 
    Iterate through the list of orders received as an input argument. 
    Return the delivery status.
    """
    for order in orders:
        order_number = order.text_content()
        tracking_page.fill("//input[@id='inputTrackingNo']",order_number)
        tracking_page.click("//button[@id='btnCheckStatus']")
        # Wait for the search result. 
        while True:
            element_text = tracking_page.locator("//tbody/tr[1]/td[2]").text_content()
            if order_number in element_text:
                break
        delivery_status = tracking_page.locator("//tbody/tr[3]/td[2]").inner_text()
        if delivery_status != "Delivered":
            break
    return delivery_status

def download_csv(): 
    """ Download the csv file into the output directory. """
    with sales_app_page.expect_download() as download_info:
        sales_app_page.get_by_text("Export").click()
    download = download_info.value
    download.save_as(CSV_PATH)

def collect_the_results(): 
    """ Upload the csv file, take a screenshot from the result and log the completion id. """
    challenge_page.bring_to_front()
    challenge_page.set_input_files("//input[@id='fileToUpload']", CSV_PATH)
    challenge_page.click("//button[@id='btnUploadFile']")
    completion_modal = challenge_page.locator("//div[@class='modal-dialog modal-confirm modal-dialog-centered']")
    browser.screenshot(completion_modal)
    completion_id = challenge_page.locator("id=guidvalue").input_value()
    log.info(f"Challenge completion id: {completion_id}")
    time.sleep(5)