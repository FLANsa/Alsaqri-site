#!/bin/bash

# Deployment Script for Mobile Phone Inventory System
# This script helps deploy the application to various platforms

echo "🚀 Starting deployment process..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit - Mobile Phone Inventory System"
fi

# Check current git status
echo "📊 Checking git status..."
git status

# Add all changes
echo "📝 Adding all changes..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Deploy: Updated VAT handling and price editing features"

# Check if remote repository exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "⚠️  No remote repository found."
    echo "Please add your remote repository first:"
    echo "git remote add origin <your-repo-url>"
    echo ""
    echo "Or deploy manually to your preferred platform:"
    echo ""
    echo "🌐 Deployment Options:"
    echo "1. Render (Recommended): https://render.com"
    echo "2. Railway: https://railway.app"
    echo "3. Heroku: https://heroku.com"
    echo "4. PythonAnywhere: https://pythonanywhere.com"
    echo ""
    echo "📋 Required Environment Variables:"
    echo "- SECRET_KEY: Your secret key for Flask"
    echo "- DATABASE_URL: PostgreSQL database URL (auto-provided by platform)"
    echo "- PORT: Port number (auto-provided by platform)"
    echo ""
    echo "🔧 Manual Deployment Steps:"
    echo "1. Push to your repository: git push origin main"
    echo "2. Connect your repository to your chosen platform"
    echo "3. Set environment variables in platform dashboard"
    echo "4. Deploy!"
else
    echo "📤 Pushing to remote repository..."
    git push origin main
    echo "✅ Code pushed successfully!"
    echo ""
    echo "🌐 Next steps:"
    echo "1. Go to your deployment platform dashboard"
    echo "2. Set the environment variables:"
    echo "   - SECRET_KEY: Generate a secure random key"
    echo "   - DATABASE_URL: Will be auto-provided"
    echo "   - PORT: Will be auto-provided"
    echo "3. Deploy your application"
fi

echo ""
echo "🎉 Deployment script completed!"
echo "📞 For support, check the DEPLOYMENT_GUIDE.md file"
