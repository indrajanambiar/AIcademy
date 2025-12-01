#!/bin/bash
# Quick script to monitor RAG usage in real-time

echo "🔍 Monitoring RAG Usage - Press Ctrl+C to stop"
echo "================================================"
echo ""
echo "Legend:"
echo "  ✅ = Using PDF knowledge (RAG + LLM)"
echo "  ⚠️  = Using LLM knowledge only (No PDFs)"
echo ""
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Monitor the uvicorn logs
# This assumes you're running uvicorn in the backend directory
# Adjust the log source as needed

tail -f /dev/null 2>&1 | while read line; do
    # Check for RAG context found
    if echo "$line" | grep -q "RAG CONTEXT FOUND"; then
        echo -e "${GREEN}✅ RAG ACTIVE${NC} - Using PDF knowledge"
        echo "$line" | grep -o 'sources.*' | head -1
        echo "$line" | grep -o 'chunks_retrieved.*' | head -1
        echo ""
    fi
    
    # Check for no RAG context
    if echo "$line" | grep -q "NO RAG CONTEXT"; then
        echo -e "${YELLOW}⚠️  LLM ONLY${NC} - No PDF knowledge found"
        echo "$line" | grep -o 'subject.*' | head -1
        echo ""
    fi
    
    # Check for generation start
    if echo "$line" | grep -q "Starting.*generation"; then
        echo -e "${BLUE}🎯 GENERATING${NC}"
        echo "$line" | grep -o 'material_type.*' | head -1
        echo "$line" | grep -o 'subject.*' | head -1
        echo ""
    fi
done
