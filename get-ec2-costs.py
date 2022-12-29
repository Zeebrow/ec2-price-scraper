# https://www.simplilearn.com/tutorials/python-tutorial/selenium-with-python
import time
from datetime import datetime
import csv
from pathlib import Path
from math import floor, ceil
from typing import List
import shutil
import zipfile
import os

import boto3 
from pyautogui import hotkey
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.service import Service
from selenium import webdriver

"""
Scrapes pricing information for EC2 instance types for available regions.
Data for all regions (28) of a single operating system uses between 588K - 712K of disk space.
"""
###############################################################################
# globals, constants
###############################################################################
# DATABASE = 'ec2-costs.db'
# DWH_DATABASE = 'ec2-costs-dwh.db'
# MAIN_TABLE_NAME = 'ec2_costs'
t_prog_start = time.time()
OPERATING_SYSTEMS = None # 'None' to scrape ['Linux', 'Windows']
REGIONS = None # 'None' to scrape all regions
CSV_DATA_DIR = Path('csv-data/ec2')
TIMESTAMP = floor(time.time())
PAGE_LOAD_DELAY = 5 #seconds
WAIT_BETWEEN_COMMANDS = 1 #seconds
URL = "https://aws.amazon.com/ec2/pricing/on-demand/"
human_date = datetime.fromtimestamp(TIMESTAMP).strftime("%Y-%m-%d") # date -I

UPLOAD_BUCKET_REGION = 'us-east-1'
UPLOAD_BUCKET_NAME = 'quickhost-pricing-data'
AWS_PROFILE = 'quickhost-ci-admin'

###############################################################################
# set up storage
###############################################################################
# db = EC2CostsDatabase(db_name=DATABASE, main_table_name=MAIN_TABLE_NAME)
# dwh = EC2CostsDWH(ts=TIMESTAMP, dwh_db_name=DWH_DATABASE, dwh_main_table_name=MAIN_TABLE_NAME)
# db.nuke_tables()
# db.create_tables()
# dwh.create_tables()
# dwh_tgt_table = dwh.new_dwh_table()

###############################################################################
# init Firefox driver
###############################################################################
# print("Some actions cannot be automated. please follow instructions as they are given.")
# print("Please wait for the browser to zoom out before moving it or changing focus away from it.")
options = webdriver.FirefoxOptions()
options.binary_location = '/usr/bin/firefox-esr'
driverService = Service('/usr/local/bin/geckodriver')
driver = webdriver.Firefox(service=driverService, options=options)
driver.get(URL)
# print(f"beginning in {str(PAGE_LOAD_DELAY)} seconds...")
time.sleep(PAGE_LOAD_DELAY)
# print('starting program')

###############################################################################
# classes and functions
###############################################################################
class MyScreen:
    PADDING_AMT = 3
    def __init__(self, w=None, h=None) -> None:
        self.w, self.h = os.get_terminal_size()
        if w is not None:
            self.w = int(w)
        if h is not None:
            self.h = int(h)
        self.lines = []
        for il in range(self.h):
            self.lines.append([])
            self.set_line(il, f"{il})...")
        self.draw_screen()

    def set_line(self,lineno:int, msg: str):
        self.lines[lineno] = msg + " "*(self.w - len(msg) - MyScreen.PADDING_AMT) + '\n'

    def clear(self):
        [print() for l in self.lines]

    def draw_screen(self):
        for l in self.lines:
            print(''.join(l), end='')
        for l in self.lines:
            print("\x1b[1A", end='')
class Instance:
    def __init__(self, region: str, operating_system:str, instance_type: str , cost_per_hr:str , cpu_ct:str , ram_size:str , storage_type:str , network_throughput: str) -> None:
        self.region = region
        self.operating_system = operating_system
        self.instance_type = instance_type
        self.cost_per_hr = cost_per_hr
        self.cpu_ct = cpu_ct
        self.ram_size = ram_size
        self.storage_type = storage_type
        self.network_throughput = network_throughput
        self.split_instance_type()
    def __repr__(self) -> str:
        return f"{self.instance_type} {self.operating_system} {self.region}"
    def split_instance_type(self):
        x, self.instance_size = self.instance_type.split(".")
        self.instance_family = x[0]
        self.instance_generation = x[1]
        self.instance_attributes = None
        if len(x) > 2:
            self.instance_attributes = x[2:]

    @classmethod
    def get_instance_details_fields(self):
        return [
            "instance_type",
            "instance_size",
            "instance_family",
            "instance_generation",
            "instance_attributes",
            "operating_system",
            "region",
            "cost_per_hr",
            "cpu_ct",
            "ram_size_gb",
            "storage_type",
            "network_throughput",
        ]
    @classmethod
    def get_csv_fields(self):
        return [
            "instance_type",
            "operating_system",
            "region",
            "cost_per_hr",
            "cpu_ct",
            "ram_size_gb",
            "storage_type",
            "network_throughput"
        ]

    def instance_details_dict(self):
        return {
            "instance_type": self.instance_type,
            "instance_size": self.instance_size,
            "instance_family": self.instance_family,
            "instance_generation": self.instance_generation,
            "instance_attributes": self.instance_attributes,
            "operating_system": self.operating_system,
            "region": self.region,
            "cost_per_hr": self.cost_per_hr,
            "cpu_ct": self.cpu_ct,
            "ram_size_gb": self.ram_size,
            "storage_type": self.storage_type,
            "network_throughput": self.network_throughput,
        }
    def as_dict(self):
        return {
            "instance_type": self.instance_type,
            "operating_system": self.operating_system,
            "region": self.region,
            "cost_per_hr": self.cost_per_hr,
            "cpu_ct": self.cpu_ct,
            "ram_size_gb": self.ram_size,
            "storage_type": self.storage_type,
            "network_throughput": self.network_throughput,
        }

class NavSection:
    ON_DEMAND_PRICING = "On-Demand Pricing"
    DATA_TRANSFER = "Data Transfer"
    DATA_TRANSFER_WITHIN_THE_SAME_AWS_REGION = "Data Transfer within the same AWS Region"
    EBS_OPTIMIZED_INSTANCES = "EBS-Optimized Instances"
    ELASTIC_IP_ADDRESSES = "Elastic IP Addresses"
    CARRIER_IP_ADDRESSES = "Carrier IP Addresses"
    ELASTIC_LOAD_BALANCING = "Elastic Load Balancing"
    ON_DEMAND_CAPACITY_RESERVATIONS = "On-Demand Capacity Reservations"
    T2_T3_T4G_UNLIMITED_MODE_PRICING = "T2/T3/T4g Unlimited Mode Pricing"
    AMAZON_CLOUDWATCH = "Amazon CloudWatch"
    AMAZON_ELASTIC_BLOCK_STORE = "Amazon Elastic Block Store"
    AMAZON_EC2_AUTO_SCALING = "Amazon EC2 Auto Scaling"
    AWS_GOVCLOUD_REGION = "AWS GovCloud Region"

def use_iframe(f):
    def iframe_func(*args, **kwargs):
        driver.switch_to.default_content()
        iframe = driver.find_element('id', "iFrameResizer0")
        driver.switch_to.frame(iframe)
        r = f(*args, **kwargs)
        driver.switch_to.default_content()
        return r
    return iframe_func

def zoom_browser():
    hotkey('ctrl', '-')
    hotkey('ctrl', '-')
    hotkey('ctrl', '-')
    hotkey('ctrl', '-')
    hotkey('ctrl', '-')
    hotkey('ctrl', '-')
    time.sleep(3)

def nav_to(section: NavSection):
    """select a section to mimic scrolling"""
    sidebar = driver.find_element(By.CLASS_NAME, 'lb-sidebar-content')
    for elem in sidebar.find_elements(By.XPATH, 'div/a'):
        if elem.text.strip() == section:
            elem.click()
            time.sleep(WAIT_BETWEEN_COMMANDS)
            return
    raise Exception(f"no such section '{section}'")

@use_iframe
def get_available_operating_systems() -> List[str]:
    """get all operating systems for filtering data"""
    available_operating_systems = []
    os_selection_box = driver.find_element(By.ID, 'awsui-select-2')
    os_selection_box.click()
    time.sleep(WAIT_BETWEEN_COMMANDS)
    for elem in driver.find_element(By.ID, 'awsui-select-2-dropdown').find_elements(By.CLASS_NAME, 'awsui-select-option-label'):
        available_operating_systems.append(elem.text)
    # collapse
    os_selection_box.click()
    time.sleep(WAIT_BETWEEN_COMMANDS)
    return available_operating_systems
    
@use_iframe
def select_operating_system(os: str):
    """select an operating system for filtering data"""
    os_selection_box = driver.find_element(By.ID, 'awsui-select-2')
    os_selection_box.click()
    time.sleep(WAIT_BETWEEN_COMMANDS)
    for elem in driver.find_element(By.ID, 'awsui-select-2-dropdown').find_elements(By.CLASS_NAME, 'awsui-select-option-label'):
        if elem.text == os:
            elem.click()
            time.sleep(WAIT_BETWEEN_COMMANDS)
            return
    raise Exception(f"No such operating system: '{os}'")

@use_iframe
def get_available_regions() -> List[str]:
    """get all aws regions for filtering data"""
    available_regions = []
    region_selection_box = driver.find_element('id', 'awsui-select-1-textbox')
    region_selection_box.click()
    time.sleep(WAIT_BETWEEN_COMMANDS)
    for elem in driver.find_elements(By.CLASS_NAME, 'awsui-select-option-label-tag'):
        available_regions.append(elem.text)
    region_selection_box.click()
    time.sleep(WAIT_BETWEEN_COMMANDS)
    return available_regions

@use_iframe
def select_aws_region_dropdown(region: str):
    """Set the table of data to display for a given aws region"""
    ################
    # Location Type
    ################
    location_type_select_box = driver.find_element(By.ID, 'awsui-select-0')
    location_type_select_box.click()
    time.sleep(WAIT_BETWEEN_COMMANDS)

    # what you have to click firt in order to show the dropdown 
    filter_selection = 'AWS Region'
    all_filter_options = driver.find_element(By.ID, 'awsui-select-0-dropdown')
    all_filter_options.find_element(By.XPATH, f'//*[ text() = "{filter_selection}"]').click()
    time.sleep(WAIT_BETWEEN_COMMANDS)
    
    ################
    # Region
    ################
    region_select_box = driver.find_element(By.ID, 'awsui-select-1-textbox')
    region_select_box.click()
    time.sleep(WAIT_BETWEEN_COMMANDS)
    search_box = driver.find_element(By.ID, 'awsui-input-0')
    search_box.send_keys(region)
    time.sleep(WAIT_BETWEEN_COMMANDS)
    for elem in driver.find_elements(By.CLASS_NAME, 'awsui-select-option-label-tag'):
        if elem.text == region:
            #@@@ I think this is also clicking shit underneath it, vCPU
            elem.click()
            #check state of all dropdown menus are closed
            time.sleep(WAIT_BETWEEN_COMMANDS)
            return
    raise Exception(f"No such region: '{region}'")

@use_iframe
def scrape_all_(region:str, os: str) -> List[Instance]:
    """
    get all pages in iframe
    when finished searching, get number of pages.
    then iterate through them with the > arrow until num_pages 
    """
    rtn = []
    # page numbers (1, 2, 3, (literal)..., last, >)
    pages = driver.find_element(By.CLASS_NAME, 'awsui-table-pagination-content').find_elements(By.TAG_NAME, "li")
    pages[1].click() # make sure were on page 1 when this function is run more than once
    time.sleep(WAIT_BETWEEN_COMMANDS)
    arrow_button = pages[-1] # >
    num_pages = pages[-2].find_element(By.TAG_NAME, 'button').text # last page number

    for i in range(int(num_pages)):
        # only cycle to next page after it has been scraped
        if i > 0:
            arrow_button.click()
            time.sleep(0.2)
        selection = driver.find_element(By.TAG_NAME, 'tbody')
        # rows in HTML table
        tr_tags = selection.find_elements(By.TAG_NAME, 'tr')
        for tr in tr_tags:
            instance_props = []
            # columns in row
            for td in tr.find_elements(By.TAG_NAME, "td"):
                # 0 t3a.xlarge
                # 1 $0.1699
                # 2 4
                # 3 16 GiB
                # 4 EBS Only
                # 5 Up to 5 Gigabit
                instance_props.append(td.text)
            instance = Instance(region, os, *instance_props)
            # instance.store(db.conn, MAIN_TABLE_NAME)
            # instance.store(conn=dwh.conn, main_table_name=MAIN_TABLE_NAME, dwh_timestamp_suffix=TIMESTAMP)
            rtn.append(instance)
        time.sleep(0.2)
    return rtn

@use_iframe
def get_result_count_test() -> int:
    """get the 'Viewing ### of ### Available Instances' count to check our results"""
    t =  driver.find_element(By.CLASS_NAME, 'awsui-table-header').find_element(By.TAG_NAME, "h2").text
    # ¯\_(ツ)_/¯
    return int(t.split("of")[1].split(" available")[0].strip())

def s3_upload(zipfile_dir: Path) -> int:
    """returns number of files uploaded"""
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=UPLOAD_BUCKET_REGION)
    s3 = session.client('s3')
    rtn_file_ct = 0
    for zipf in zipfile_dir.iterdir():
        if zipf.name.endswith(".zip"):
            s3.upload_file(str(zipf.relative_to('.')), UPLOAD_BUCKET_NAME, str(zipf.relative_to('.')))
            rtn_file_ct += 1
    return rtn_file_ct


###############################################################################
# main-ish
###############################################################################
if REGIONS:
    tgt_regions = REGIONS
else:
    tgt_regions = get_available_regions()

if OPERATING_SYSTEMS:
    tgt_operating_systems = OPERATING_SYSTEMS
else:
    tgt_operating_systems = ['Linux', 'Windows']

base_scrape_dir = Path(CSV_DATA_DIR / human_date)
if base_scrape_dir.exists():
    # print(f"Deleting old data in '{base_scrape_dir}'")
    shutil.rmtree(base_scrape_dir)

screen_os_lines = {}
for n, r in enumerate(tgt_operating_systems):
    # 2 for title and "OS" heading
    screen_os_lines[r] = n+2
screen_regions_lines = {}
for n, r in enumerate(tgt_regions):
    # 2 for title and "OS" heading
    # 1 for "Regions" heading
    screen_regions_lines[r] = n+2+len(tgt_operating_systems)+1

line_count = len(tgt_operating_systems) + len(tgt_regions) + 3 + 2
screen = MyScreen(h=(len(tgt_operating_systems) + len(tgt_regions) + 3 + 2))
screen.set_line(0, "Scraperdoodle")
screen.set_line(1, "OS:")
for t, n in screen_os_lines.items():
    screen.set_line(n, f"- {t}")
screen.set_line(2+len(tgt_operating_systems), "Regions:")
for t, n in screen_regions_lines.items():
    screen.set_line(n, f"- {t}")
screen.set_line(line_count-2, "")
screen.set_line(line_count-1, "Status: starting...")
status_line = line_count - 1
screen.draw_screen()
zoom_browser()
nav_to(NavSection.ON_DEMAND_PRICING)

# print()
# print(f"Operating Systems ({len(tgt_operating_systems)}):")
# [print(f"- {r}") for r in tgt_operating_systems]
# print()
# print(f"Regions ({len(tgt_regions)}):")
# [print(f"- {r}") for r in tgt_regions]
# print()

total_instance_count = 0

for o_num, _os in enumerate(tgt_operating_systems):
    screen.set_line(status_line, f"setting operating system")
    screen.draw_screen()
    select_operating_system(_os)
    screen.set_line(screen_os_lines[_os], f"\033[93m- {_os}\033[0m")
    screen.draw_screen()
    # NOTE: this is where the directory structure is determined
    tgt_csv_data_dir = CSV_DATA_DIR / human_date / _os
    tgt_csv_data_dir.mkdir(parents=True, exist_ok=True)

    ###########################
    # Write csv file per region
    ###########################
    for r_num, region in enumerate(tgt_regions):
        # NOTE: if the selected region was not visible in the drop-down menu at the time it was clicked,
        # the page seems to jump back to the top. Happened on ca-central-1. There are also fancy dividers
        # between some regions
        screen.set_line(status_line, f"setting region to {region}")
        screen.draw_screen()
        select_aws_region_dropdown(region=region)
        t_region_scrape_start = time.time()
        screen.set_line(screen_regions_lines[region], f"\033[93m- {region}\033[0m")
        screen.set_line(status_line, f"scraping {region}...")
        screen.draw_screen()
        stuff = scrape_all_(region=region, os=_os)
        t_region_scrape = ceil(time.time() - t_region_scrape_start)
        if len(stuff) != get_result_count_test():
            screen.set_line(screen_regions_lines[region], f"\033[94m- {region} BAD DATA: (*{len(stuff)}* instances in {t_region_scrape} sec)\033[0m")
        #     print("\033[31mWARNING: possibly got bad data - make sure every thing in the 'On-Demand Plans for EC2' section is visible, and rerun\033[0m")
        total_instance_count += len(stuff)
        screen.set_line(screen_regions_lines[region], f"\033[93m- {region} ({len(stuff)} instances in {t_region_scrape} sec)\033[0m")
        screen.set_line(status_line, f"writing csv data...")
        screen.draw_screen()
        f = tgt_csv_data_dir / f"{region}.csv"
        with f.open('w') as cf:
            fieldnames = Instance.get_csv_fields()
            # don't need these fields, they are included in the filepath
            fieldnames.remove("region")
            fieldnames.remove("operating_system")
            writer = csv.DictWriter(cf, fieldnames=fieldnames)
            writer.writeheader()
            for inst in stuff:
                row = inst.as_dict()
                row.pop("region")
                row.pop("operating_system")
                writer.writerow(row)
        _et = ceil(time.time() - t_prog_start)
        et = f"{floor(_et/60)}:{_et%60:02}"
        screen.set_line(screen_regions_lines[region], f"\033[92m- {region} ({len(stuff)} instances in {t_region_scrape} sec) (saved to file '{f.relative_to('.')}')\033[0m")
        screen.set_line(status_line, f"finished scraping {region}")
        screen.draw_screen()
        # print(f"\033[36m{et} - processed {len(stuff)} {_os} ({o_num+1}/{len(tgt_operating_systems)}) instances for {region} ({r_num+1}/{len(tgt_regions)}) in {t_region_scrape} seconds.\033[0m")

    screen.set_line(screen_os_lines[_os], f"\033[92m- {_os}\033[0m")
    screen.draw_screen()
    ###########################
    # zip the csv files per os
    ###########################
    zip_archive = f"{_os}_{human_date}.bz2.zip"
    with zipfile.ZipFile(str(base_scrape_dir / zip_archive), 'w', compression=zipfile.ZIP_BZIP2) as zf:
        for csv_file in tgt_csv_data_dir.iterdir():
            zf.write(csv_file.relative_to('.'))
    # print(f"Compressed data: {str(base_scrape_dir/zip_archive)}")

screen.clear()
###########################
# upload zips to s3
###########################
num_files_uploaded = s3_upload(base_scrape_dir)
# print(f"\033[92mUploaded {num_files_uploaded} files to s3 bucket '{UPLOAD_BUCKET_NAME} ({UPLOAD_BUCKET_REGION})'\033[0m")

t_prog_end = ceil(time.time() - t_prog_start)
driver.close()
# print()
# print(f"\033[92mProgram finished in {t_prog_end} seconds\033[0m")
# print(f"\033[36m{total_instance_count} instances were scraped for {len(tgt_operating_systems)} operating systems in {len(tgt_regions)} regions.\033[0m")