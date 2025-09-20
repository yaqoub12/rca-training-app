# 🚀 RCA Training Deployment Guide

## Quick Start for Training Sessions

### Step 1: Prepare Repository
1. **Create GitHub Repository**:
   ```bash
   # Initialize git in your project folder
   git init
   git add .
   git commit -m "Initial commit - RCA Risk Assessment App for Training"
   
   # Create repository on GitHub and push
   git remote add origin https://github.com/yourusername/rca-training-app.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy to Railway (Recommended)

#### Why Railway?
- ✅ **Free tier**: Perfect for training sessions
- ✅ **Auto-deployment**: Connects directly to GitHub
- ✅ **Fast setup**: Live in under 5 minutes
- ✅ **Reliable**: Good uptime for training sessions

#### Deployment Steps:
1. **Visit Railway**: Go to [railway.app](https://railway.app)
2. **Sign up**: Use your GitHub account
3. **Deploy**: Click "Deploy from GitHub repo"
4. **Select**: Choose your RCA training repository
5. **Configure**: Railway auto-detects `railway.toml`
6. **Wait**: Deployment takes 2-3 minutes
7. **Access**: Your app will be at `https://your-app-name.railway.app`

### Step 3: Multiple Training Groups

#### Create Separate Deployments:
For each training session, create a new Railway deployment:

1. **Group 1**: `rca-training-session-1`
   - URL: `https://rca-training-session-1.railway.app`
   
2. **Group 2**: `rca-training-session-2`
   - URL: `https://rca-training-session-2.railway.app`
   
3. **Group 3**: `rca-training-session-3`
   - URL: `https://rca-training-session-3.railway.app`

#### Benefits:
- 🔒 **Isolated environments** - No data conflicts
- 🔄 **Fresh data** - Each group starts clean
- 👥 **Concurrent sessions** - Multiple groups can train simultaneously
- 📊 **Individual progress** - Each group's work is separate

### Step 4: Share with Trainees

#### Training Session Setup:
1. **Share URL**: Give each group their specific URL
2. **Test Access**: Verify all trainees can access the app
3. **Demo Features**: Show key functionality:
   - Load Work Order
   - Import Sample MS
   - Select Hazards (organized by categories)
   - Apply Controls (with parameters)
   - Evaluate Risk Matrix
   - Select Personnel at Risk

### Step 5: Training Scenarios

#### Pre-loaded Content:
- ✅ **21 Hazards**: Electrical, Mechanical, Chemical, Physical, etc.
- ✅ **50+ Controls**: Following hierarchy (Elimination → PPE)
- ✅ **6 Personnel Types**: Maintenance, Operations, Contractors, etc.
- ✅ **Risk Matrix**: 5×5 with color coding
- ✅ **Sample Work Order**: Pump overhaul scenario

#### Training Exercises:
1. **Basic Risk Assessment**: Use sample work order
2. **Custom Scenarios**: Create new work orders
3. **Parameter Practice**: Use hazards/controls with parameters
4. **Risk Evaluation**: Practice likelihood × severity
5. **Control Selection**: Apply hierarchy of controls

## Alternative Deployment Options

### Option 2: Render.com
- Free tier available
- Uses `render.yaml` configuration
- Slightly slower deployment than Railway

### Option 3: Heroku
- Free tier discontinued (paid plans only)
- Uses `Procfile` configuration
- More complex setup

### Option 4: Docker (Advanced)
- Use provided `Dockerfile`
- Deploy to any container platform
- More technical setup required

## Troubleshooting

### Common Issues:
1. **App won't start**: Check logs for database initialization errors
2. **Empty catalogs**: Run deployment initialization script
3. **Access denied**: Verify repository is public or deployment has access

### Support:
- Check deployment logs in Railway/Render dashboard
- Verify all required files are in repository
- Ensure `scripts/deploy_init.py` runs successfully

## Training Session Checklist

### Before Training:
- [ ] Repository created and pushed to GitHub
- [ ] Deployment(s) created and tested
- [ ] URLs shared with trainees
- [ ] Sample scenarios prepared
- [ ] Backup deployment ready (if needed)

### During Training:
- [ ] Monitor deployment status
- [ ] Help trainees access their URLs
- [ ] Guide through key features
- [ ] Collect feedback for improvements

### After Training:
- [ ] Optional: Keep deployments for reference
- [ ] Optional: Export data if needed
- [ ] Optional: Create new deployments for next session

---

## 🎯 Ready for Training!

Your RCA Risk Assessment app is now ready for professional training sessions. Each group gets their own isolated environment with comprehensive HSE catalogs and realistic scenarios.

**Happy Training! 🛡️**
