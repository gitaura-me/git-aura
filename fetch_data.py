"""
This script fetches data from the github API and saves it to a local file.
This python file should be run from the parent directory.
"""

import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd
import datetime
from bs4 import BeautifulSoup


def tprint(message):
    print(f"{datetime.datetime.now()}: " + message)

def fetch_contributions(username):
    url = f"https://github.com/users/{username}/contributions"

    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        contributions = soup.find_all('h2', class_='f4 text-normal mb-2')
        contributions = contributions[0].text.replace(',', '')
        contributions_int = int(contributions.split()[0])
    else:
        contributions_int = 0

    return contributions_int
    

if __name__ == "__main__":
    # Load the environment variables
    load_dotenv()
    # Get the github token
    token = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')

    # Create data directory if it does not exist
    if not os.path.exists('data'):
        os.makedirs('data')

    headers = {
        'Authorization': f'token {token}'
    }
    
    url = 'https://api.github.com/users?per_page=100'
    users = []
    id_multiplier = 100000
    pagination = 100
    num_pages = 10
    for i in range(1, num_pages + 1):
        tprint(f"Fetching data for page (since parameter): {i * id_multiplier}")
        response = requests.get(url, headers=headers, params={'since': i * id_multiplier, 'per_page': pagination})
        if response.status_code == 200:
            user_data = response.json()
            for user in user_data:
                user_info = {}
                user_info['login'] = user['login']
                user_info['link'] = user['html_url']
                tprint(f"Fetching data for user: {user_info['login']}")

                # Fetch user details
                user_url = user['url']
                user_response = requests.get(user_url, headers=headers)
                if user_response.status_code == 200:
                    user_details = user_response.json()
                    user_info['followers'] = user_details['followers']
                    user_info['following'] = user_details['following']

                    user_info['follow_ratio'] = user_info['followers'] / user_info['following'] if user_info['following'] != 0 else 0

                    user_info['public_repos'] = user_details['public_repos']

                    # Fetch contributions
                    user_info['contributions'] = fetch_contributions(user_info['login'])

                    # Fetch repositories details
                    repos_url = user_details['repos_url']
                    repos_response = requests.get(repos_url, headers=headers)
                    if repos_response.status_code == 200:
                        repos = repos_response.json()
                        user_info['stars'] = sum(repo['stargazers_count'] for repo in repos)
                        user_info['total_size'] = sum(repo['size'] for repo in repos)
                        if repos:
                            most_popular_repo = max(repos, key=lambda repo: repo['stargazers_count'])
                            user_info['most_popular_repo_forked'] = most_popular_repo['fork']
                        else:
                            user_info['most_popular_repo_forked'] = False

                user_info['user_feedback'] = 0

                users.append(user_info)
                tprint(f"Data fetched for user: {user_info['login']}")

    # Check if the file exists
    file_path = 'data/users.csv'
    if os.path.exists(file_path):
        # Load the existing data
        existing_df = pd.read_csv(file_path)
        # Append the new data
        new_df = pd.DataFrame(users)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        # Create a new dataframe
        combined_df = pd.DataFrame(users)

    # Save the combined data to a csv file using pandas
    combined_df.to_csv(file_path, index=False)
    tprint('Data fetched and saved successfully')