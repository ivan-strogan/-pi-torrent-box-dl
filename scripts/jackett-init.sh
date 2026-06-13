#!/bin/bash
REPO="ivan-strogan/Jackett"
BRANCH="main"
BASE_URL="https://raw.githubusercontent.com/${REPO}/${BRANCH}/src/Jackett.Common/Content"

curl -fsSL -o /app/Jackett/Content/login.html "${BASE_URL}/login.html"
