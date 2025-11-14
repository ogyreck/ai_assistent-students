#!/usr/bin/env python3
"""Test script to verify config loading"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.chdir(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from config.Config import CONFIG
    print("✓ Config loaded successfully!")
    print(f"\nLLM Configuration:")
    print(f"  Base URL: {CONFIG.llm.url}")
    print(f"  Model: {CONFIG.llm.model}")
    print(f"  Token: {CONFIG.llm.token[:20]}..." if CONFIG.llm.token else "  Token: NOT SET")

    # Try to initialize LLM client
    from service.llm_client import create_llm_client
    client = create_llm_client(
        base_url=CONFIG.llm.url,
        api_key=CONFIG.llm.token,
        model=CONFIG.llm.model
    )
    print("\n✓ LLM Client initialized successfully!")

    # Try to initialize Whisper transcriber
    from service.whisper_service import create_whisper_transcriber
    transcriber = create_whisper_transcriber(
        api_key=CONFIG.llm.token,
        base_url=CONFIG.llm.url
    )
    print("\n✓ Whisper Transcriber initialized successfully!")
    print(f"  Original URL: {CONFIG.llm.url}")
    print(f"  Normalized URL: {transcriber.base_url}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
