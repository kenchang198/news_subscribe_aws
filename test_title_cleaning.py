#!/usr/bin/env python3
"""
Test script for the remove_site_name_from_title function
"""

from src.narration_generator import remove_site_name_from_title

# Test cases
test_cases = [
    'TechCrunch：新しいAI技術が登場',
    'Qiita: React入門ガイド',
    '【GitHub】新機能リリース',
    '[Yahoo!]ニュース記事タイトル',
    '（ZDNet）セキュリティ最新情報',
    '(Google)開発者向けツール',
    'はてなブックマーク｜人気記事',
    'Twitter|新API発表',
    'Microsoft－Azure更新',
    'Amazon-AWS新サービス',
    'Normal title without site name',
    'サイト名 : タイトル',
    '',
    None
]

print('Testing remove_site_name_from_title function:')
print('=' * 50)

for i, test_case in enumerate(test_cases):
    try:
        result = remove_site_name_from_title(test_case)
        print(f'{i+1:2d}. Input:  "{test_case}"')
        print(f'    Output: "{result}"')
        print()
    except Exception as e:
        print(f'{i+1:2d}. Input:  "{test_case}"')
        print(f'    Error:  {e}')
        print()