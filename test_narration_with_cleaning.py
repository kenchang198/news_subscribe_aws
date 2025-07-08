#!/usr/bin/env python3
"""
Test script for the narration generation with title cleaning
"""

import datetime
from src.narration_generator import generate_narration_texts

# Test articles with site names in titles
test_articles = [
    {'title': 'TechCrunch：新しいAI技術が登場'},
    {'title': 'Qiita: React入門ガイド'},
    {'title': '【GitHub】新機能リリース'},
    {'title': '[Yahoo!]ニュース記事タイトル'},
    {'title': '（ZDNet）セキュリティ最新情報'},
]

print('Testing narration generation with title cleaning:')
print('=' * 60)

today = datetime.date.today()
narrations = generate_narration_texts(today, test_articles)

for key, text in narrations.items():
    print(f'{key}:')
    print(f'  {text}')
    print()

print('Expected behavior: Site names should be removed from titles in narrations')
print('Original titles should contain site names like "TechCrunch：", "Qiita:", etc.')
print('Narration text should contain cleaned titles without site names')