import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from PIL import Image
import io
import cv2
import numpy as np
from webdriver_manager.chrome import ChromeDriverManager

# 设置日志格式，只精确到秒
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# 从环境变量获取配置
SCKEY = os.environ.get('SCKEY')
MONITOR_URL = os.environ.get('MONITOR_URL')
MONITOR_PORT = os.environ.get('MONITOR_PORT')
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', 300))  # 默认检查间隔为300秒（5分钟）

# 构建 URL，如果有端口则添加，否则使用原始 URL
URL = f"http://{MONITOR_URL}:{MONITOR_PORT}" if MONITOR_PORT else f"http://{MONITOR_URL}"

# 创建 tmp 文件夹
TMP_DIR = os.path.join(os.path.dirname(__file__), 'tmp')
os.makedirs(TMP_DIR, exist_ok=True)

def setup_driver():
    """初始化并返回 Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--font-render-hinting=none')
    chrome_options.add_argument('--lang=zh-CN')
    chrome_options.add_argument('--font-family="WenQuanYi Micro Hei, WenQuanYi Zen Hei, Noto Sans CJK SC"')
    
    try:
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    except WebDriverException as e:
        logging.error(f"WebDriver 初始化失败: {e}")
        raise

def wait_for_page_load(driver, timeout=60):
    """等待页面加载完成"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(15)  # 额外等待以确保所有动态内容加载完成
        return True
    except TimeoutException:
        logging.error("页面加载超时")
        return False

def take_screenshot(driver, filename):
    """截取当前页面并保存，文件名包含时间戳"""
    time.sleep(5)  # 等待页面稳定
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_with_timestamp = os.path.join(TMP_DIR, f"{os.path.splitext(filename)[0]}_{timestamp}{os.path.splitext(filename)[1]}")
    screenshot = driver.get_screenshot_as_png()
    Image.open(io.BytesIO(screenshot)).save(filename_with_timestamp)
    logging.info(f"截图已保存为 {filename_with_timestamp}")
    return filename_with_timestamp

def find_and_click_image(driver, template_path, screenshot_path, threshold=0.7):
    """在截图中查找模板图像并点击"""
    if not os.path.exists(template_path):
        logging.error(f"模板图片不存在: {template_path}")
        return False

    try:
        template = cv2.imread(template_path, 0)
        screenshot = cv2.imread(screenshot_path, 0)
        if template is None or screenshot is None:
            logging.error("无法读取模板图片或截图")
            return False

        scales = np.linspace(0.8, 1.2, 5)  # 多尺度匹配
        max_val, max_loc, max_scale = -np.inf, None, None

        for scale in scales:
            resized_template = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            result = cv2.matchTemplate(screenshot, resized_template, cv2.TM_CCOEFF_NORMED)
            _, local_max_val, _, local_max_loc = cv2.minMaxLoc(result)
            if local_max_val > max_val:
                max_val, max_loc, max_scale = local_max_val, local_max_loc, scale

        logging.info(f"最大匹配值: {max_val}, 最佳缩放比例: {max_scale}")

        # 在结果图像中绘制匹配区域
        result_image = cv2.imread(screenshot_path)
        h, w = [int(x * max_scale) for x in template.shape]
        cv2.rectangle(result_image, max_loc, (max_loc[0] + w, max_loc[1] + h), (0, 0, 255), 2)
        cv2.imwrite(os.path.join(TMP_DIR, "match_result.png"), result_image)

        if max_val > threshold:
            click_x, click_y = max_loc[0] + w // 2, max_loc[1] + h // 2
            driver.execute_script(f"document.elementFromPoint({click_x}, {click_y}).click();")
            logging.info(f"已点击位置: ({click_x}, {click_y})")
            return True
        else:
            logging.info(f"未找到匹配的图像，最大匹配值 {max_val} 低于阈值 {threshold}")
            return False
    except Exception as e:
        logging.error(f"图像匹配过程中发生错误: {e}")
        return False

def send_wechat_alert(title, content):
    """通过Server酱发送微信告警"""
    url = f"https://sctapi.ftqq.com/{SCKEY}.send"
    data = {
        "text": title,
        "desp": content
    }
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            logging.info(f"微信告警已发送: {title}")
            return
        except requests.RequestException as e:
            logging.error(f"发送微信告警失败 (尝试 {attempt + 1}/{retries}): {e}")
            time.sleep(5)  # 等待 5 秒后重试
    logging.error(f"微信告警发送失败: {title}")

def clear_tmp_dir():
    """清空 tmp 文件夹中的所有文件"""
    for file in os.listdir(TMP_DIR):
        file_path = os.path.join(TMP_DIR, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            logging.error(f"无法删除文件 {file_path}: {e}")

def monitor():
    """主监控逻辑"""
    logging.info("脚本运行中")
    alas_template_path = os.path.join(os.path.dirname(__file__), 'alas.png')
    start_template_paths = [os.path.join(os.path.dirname(__file__), f'start_{i}.png') for i in range(1, 3)]

    while True:
        # 清空 tmp 文件夹中的所有文件
        clear_tmp_dir()

        driver = setup_driver()
        try:
            logging.info("开始监控")
            driver.get(URL)
            
            if not wait_for_page_load(driver):
                logging.error("初始页面加载失败")
                continue
            
            home_page_screenshot = take_screenshot(driver, "home_page.png")
            
            if find_and_click_image(driver, alas_template_path, home_page_screenshot):
                logging.info("成功点击 Alas 按钮")
                if wait_for_page_load(driver):
                    after_click_alas_screenshot = take_screenshot(driver, "after_click_alas.png")
                    
                    for i, start_template_path in enumerate(start_template_paths, 1):
                        if find_and_click_image(driver, start_template_path, after_click_alas_screenshot, threshold=0.7):
                            logging.info(f"成功点击启动按钮 (使用模板{i})")
                            send_wechat_alert("Alas 监控告警", f"在 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 成功点击了启动按钮")
                            break
                    else:
                        logging.warning("未找到启动按钮或点击失败 (使用所有模板都失败)")
                else:
                    logging.error("Alas 点击后页面加载失败")
        
        except Exception as e:
            logging.error(f"监控过程中发生错误: {e}")
        finally:
            driver.quit()
        
        logging.info(f"等待 {CHECK_INTERVAL // 60} 分钟后进行下一次检查")
        time.sleep(CHECK_INTERVAL)  # 使用 CHECK_INTERVAL 变量

if __name__ == "__main__":
    logging.info("Alas 监控开始运行")
    logging.info(f"监控 {URL}")
    monitor()