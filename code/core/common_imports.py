from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import hashlib
import html
import json
import os
import re
import socket
import time

import requests
import urllib3
from jira import JIRA
from jira.exceptions import JIRAError
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
