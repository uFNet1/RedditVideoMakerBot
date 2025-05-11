#render.py
import os
from playwright.sync_api import sync_playwright, Playwright
import random
import re

# HTML Items
nsfw_html = f'''
<img src="{{nsfw_path}}" style="padding-top: 10px; flex-grow: 0; flex-shrink: 0; width: 88px; height: 27px; object-fit: cover;" />
'''

html_imports = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
"""

# HTML template with placeholders
post_template = f"""
<div id="master" style="border: 2px solid #2D3643; font-family: Noto Sans; display: flex; flex-direction: column; justify-content: flex-start; align-items: flex-start; width: 915px; position: relative; gap: 2px; padding: 15px; border-radius: 35px; background: #181d24; border-width: 1px; border-color: #2d3643;">
  <div style="display: flex; justify-content: space-between; align-items: center; align-self: stretch; flex-grow: 0; flex-shrink: 0; position: relative; padding-left: 4px; padding-right: 4px; padding-bottom: 0px;">
    <div style="display: flex; justify-content: flex-start; align-items: center; flex-grow: 0; flex-shrink: 0; position: relative; gap: 9px;">
      <img src={{pfp_directory}} style="flex-grow: 0; flex-shrink: 0; width: 36px; height: 36px; border-radius: 18px; object-fit: cover; transform: scale(1.2);" />
      <div style="line-height: 0; display: flex; flex-direction: column; justify-content: center; align-items: flex-start; flex-grow: 0; flex-shrink: 0; position: relative;">
        <div style="height: 16px; display: flex; justify-content: center; align-items: center; flex-grow: 0; flex-shrink: 0; position: relative; gap: 10px;">
          <p style="flex-grow: 0; flex-shrink: 0; font-size: 16.7px; font-weight: 600; text-align: left; color: #92a1ae;">r/{{subreddit}}</p>
          <div style="display: flex; justify-content: flex-start; align-items: center; flex-grow: 0; flex-shrink: 0; position: relative; gap: 9px;">
            <svg width="4" height="4" viewBox="0 0 4 4" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-grow: 0; flex-shrink: 0;" preserveAspectRatio="xMidYMid meet">
              <circle cx="2" cy="2" r="2" fill="#506A87"></circle>
            </svg>
            <p style="flex-grow: 0; flex-shrink: 0; font-size: 16px; text-align: left; color: #506a87;">{{time}}</p>
          </div>
        </div>
        <p style="flex-grow: 0; flex-shrink: 0; font-size: 16.7px; font-weight: 380; text-align: left; color: #92a1ae;">{{author}}</p>
      </div>
    </div>
    <div style="flex-grow: 0; flex-shrink: 0; width: 30px; height: 7.5px; position: relative; overflow: hidden; background: url({{more_path}}); background-size: cover; background-repeat: no-repeat; background-position: center;"></div>
  </div>
  <div style="display: flex; justify-content: center; align-items: center; flex-grow: 0; flex-shrink: 0; width: 865px; position: relative; gap: 10px; padding-left: 7px; padding-right: 7px;">
    <p style="flex-grow: 1; width: 851px; font-size: 25.3px; font-weight: 600; text-align: left; color: #bec2c4;">{{prompt}}</p>
  </div>
  <div style="line-height: 0px; display: flex; justify-content: flex-start; align-items: flex-end; flex-grow: 0; flex-shrink: 0; width: 398px; gap: 9px; padding-left: 6px; padding-right: 6px; padding-top: 0px;">
    <div style="display: flex; justify-content: center; align-items: center; flex-grow: 0; flex-shrink: 0; height: auto px; position: relative; gap: 8px; padding-left: 16px; padding-right: 16px; padding-top: 12px; padding-bottom: 12px; border-radius: 30px; background: #1f262e;">
      <div style="flex-grow: 0; flex-shrink: 0; width: 18px; height: 19.98px; position: relative; overflow: hidden; background: url({{upvote_path}}); background-size: cover; background-repeat: no-repeat; background-position: center;"></div>
      <p style="flex-grow: 0; flex-shrink: 0; font-size: 15.1px; font-weight: 600; text-align: left; color: #bbc0c0;">{{upvotes}}</p>
      <div style="flex-grow: 0; flex-shrink: 0; width: 18px; height: 19.98px; position: relative; overflow: hidden; background: url({{downvote_path}}); background-size: cover; background-repeat: no-repeat; background-position: center;"></div>
    </div>
  </div>
</div>
"""
comment_template = f"""
<div id="master" style="border: 2px solid #2D3643; font-family: Noto Sans; display: flex; flex-direction: column; justify-content: flex-start; align-items: flex-start; width: 915px; position: relative; gap: 2px; padding: 15px; border-radius: 35px; background: #181d24; border-width: 1px; border-color: #2d3643;">
  <div style="display: flex; justify-content: space-between; align-items: center; align-self: stretch; flex-grow: 0; flex-shrink: 0; position: relative; padding-left: 4px; padding-right: 4px; padding-bottom: 10px;">
    <div style="display: flex; justify-content: flex-start; align-items: center; flex-grow: 0; flex-shrink: 0; position: relative; gap: 9px;">
      <img src={{pfp_directory}} style="flex-grow: 0; flex-shrink: 0; width: 36px; height: 36px; border-radius: 18px; object-fit: cover; transform: scale(1.2);" />
      <div style="line-height: 0; display: flex; flex-direction: column; justify-content: center; align-items: flex-start; flex-grow: 0; flex-shrink: 0; position: relative;">
        <div style="height: 16px; display: flex; justify-content: center; align-items: center; flex-grow: 0; flex-shrink: 0; position: relative; gap: 10px;">
          <p style="flex-grow: 0; flex-shrink: 0; font-size: 16.7px; font-weight: 380; text-align: left; color: #92a1ae;">{{comment_author}}</p>
          <div style="display: flex; justify-content: flex-start; align-items: center; flex-grow: 0; flex-shrink: 0; position: relative; gap: 9px;">
            <svg width="4" height="4" viewBox="0 0 4 4" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-grow: 0; flex-shrink: 0;" preserveAspectRatio="xMidYMid meet">
              <circle cx="2" cy="2" r="2" fill="#506A87"></circle>
            </svg>
            <p style="flex-grow: 0; flex-shrink: 0; font-size: 16px; text-align: left; color: #506a87;">{{time}}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <div style="display: flex; justify-content: center; align-items: center; flex-grow: 0; flex-shrink: 0; width: 865px; position: relative; gap: 10px; padding-left: 7px; padding-right: 7px;">
    <p style="flex-grow: 1; width: 851px; font-size: 25.3px; font-weight: 600; text-align: left; color: #bec2c4;">{{comment_text}}</p>
  </div>
  <div style="line-height: 0px; display: flex; justify-content: flex-start; align-items: center; flex-grow: 0; flex-shrink: 0; width: max-content; gap: 9px; padding-left: 6px; padding-right: 6px; padding-top: 0px;">
    <div style="display: flex; justify-content: center; align-items: center; flex-grow: 0; flex-shrink: 0; height: auto px; position: relative; gap: 8px; padding-left: 16px; padding-right: 16px; padding-top: 12px; padding-bottom: 12px; border-radius: 30px; background: #1f262e;">
      <div style="flex-grow: 0; flex-shrink: 0; width: 18px; height: 19.98px; position: relative; overflow: hidden; background: url({{upvote_path}}); background-size: cover; background-repeat: no-repeat; background-position: center;"></div>
      <p style="flex-grow: 0; flex-shrink: 0; font-size: 15.1px; font-weight: 600; text-align: left; color: #bbc0c0;">{{comment_upvote_count}}</p>
      <div style="flex-grow: 0; flex-shrink: 0; width: 18px; height: 19.98px; position: relative; overflow: hidden; background: url({{downvote_path}}); background-size: cover; background-repeat: no-repeat; background-position: center;"></div>
    </div>
</div>
"""
base_directory = os.getcwd()
print(base_directory)
assets_directory = os.path.join(base_directory, 'assets')
def get_relative_asset_path(html_file_path, asset_file_name):
    # Find the relative path from the HTML file to the assets directory
    relative_path_to_assets = os.path.relpath(assets_directory, os.path.dirname(html_file_path)).replace('\\', '/')
    
    # Return the full relative path to the asset
    path = base_directory.replace('\\', '/')
    return f"{path}/assets/{asset_file_name}"

def render_data(text, pathtosave):   
    
    # Write the post HTML to a temporary file in "temp_files"
    temp_post_file = 'assets/temp/post.html'
    print(get_relative_asset_path(temp_post_file, 'upvote.png'))
    # Generate HTML for the post
    post_html = post_template.format(
        subreddit = 'StoryVault',
        author = 'User',
        prompt = text,
        upvotes = "",
        pfp_directory = get_relative_asset_path(temp_post_file, "pfp.png"),
        time = "",
        
        upvote_path = get_relative_asset_path(temp_post_file, 'upvote.png'),
        comment_path = get_relative_asset_path(temp_post_file, 'comment.png'),
        downvote_path = get_relative_asset_path(temp_post_file, 'downvote.png'),
        more_path = get_relative_asset_path(temp_post_file, 'more.png'),
    )
    post_html = f"{html_imports}{post_html}" #adding google api fonts
    
    with open(temp_post_file, 'w', encoding='utf-8') as file:
        file.write(post_html)

    # Render the post
    with sync_playwright() as playwright:
        run(playwright, temp_post_file, pathtosave)

def run(playwright: Playwright, temp_file, pathtosave):
    chromium = playwright.chromium
    browser = chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(f"file://{os.path.abspath(temp_file)}")
    
    # Save screenshot in the specific folder
    page.locator("id=master").screenshot(path=pathtosave, omit_background=True)
    
    browser.close()

# render_data('Test post 123 Test reddit ashdjlkash djkashdkjashdk hasjdh asjdhajsdhasj hdasjdhasjdh.', f"assets/temp/comment_test.png")