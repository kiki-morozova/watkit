// API base URL
const API_BASE_URL = '';

// Get package name from URL
function getPackageNameFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('name');
}

// Load package details
async function loadPackageDetails() {
    const packageName = getPackageNameFromUrl();
    
    if (!packageName) {
        displayError('No package name provided');
        return;
    }
    
    try {
        // Update page title
        document.getElementById('pageTitle').textContent = `watkit - ${packageName}`;
        
        // Load package info from search API
        const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(packageName)}&by=name`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const packageToFetch = data.results.find(p => p.name === packageName);
        
        if (!packageToFetch) {
            displayError('Package not found');
            return;
        }
        
        displayPackageInfo(packageToFetch);
        
        // Load package manifest for latest version and pass versions for display
        await loadPackageManifest(packageName, packageToFetch.latest, packageToFetch.versions || [packageToFetch.latest]);
        
    } catch (error) {
        console.error('Error loading package:', error);
        displayError('Failed to load package details');
    }
}

// Display package information
function displayPackageInfo(packageToFetch) {
    document.getElementById('packageName').textContent = packageToFetch.name;
    document.getElementById('packageAuthor').textContent = `by ${packageToFetch.author}`;
    document.getElementById('packageVersion').textContent = `v${packageToFetch.latest}`;
    
    // Display download count if available
    const downloads = packageToFetch.downloads || 0;
    const formattedDownloads = formatDownloadCount(downloads);
    document.getElementById('packageDownloads').innerHTML = `
        <i class="fas fa-download"></i>
        ${formattedDownloads} downloads
    `;
}

// Load package manifest
async function loadPackageManifest(packageName, version, versions) {
    try {
        // Get S3 bucket name from server config
        const configResponse = await fetch('/config');
        if (!configResponse.ok) {
            throw new Error('Failed to load server configuration');
        }
        const config = await configResponse.json();
        const BUCKET = config.s3_bucket_name;
        
        if (!BUCKET) {
            throw new Error('S3 bucket name not configured');
        }
        
        const s3Url = `https://${BUCKET}.s3-website-us-east-1.amazonaws.com/${packageName}/${version}/watkit.json`;
        const response = await fetch(s3Url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const manifest = await response.json();
        displayPackageContent(manifest, versions);
        
    } catch (error) {
        console.error('Error loading manifest:', error);
        displayPackageContent({ description: 'No description available' }, versions);
    }
}

// Display package content
function displayPackageContent(manifest, versions) {
    const contentDiv = document.getElementById('packageContent');
    
    const description = manifest.description || 'No description available';
    
    // Format versions list
    const versionsList = versions.map(v => `v${escapeHtml(v)}`).join(', ');
    
    contentDiv.innerHTML = `
        <div class="package-description-section">
            <h3>Description</h3>
            <p>${escapeHtml(description)}</p>
        </div>
        <div class="package-details">
            <h3>Details</h3>
            <div class="detail-item">
                <strong>Versions:</strong> ${versionsList}
            </div>
            ${manifest.license ? `<div class="detail-item"><strong>License:</strong> ${escapeHtml(manifest.license)}</div>` : ''}
        </div>
    `;
}


// Install package
function installPackage() {
    const packageName = getPackageNameFromUrl();
    const version = document.getElementById('packageVersion').textContent.replace('v', '');
    
    const command = `watkit install ${packageName}v${version}`;
    
    // Create a temporary textarea to copy the command
    const textarea = document.createElement('textarea');
    textarea.value = command;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    
    // Display the command under the button
    const packageActions = document.querySelector('.package-actions');
    
    // Remove any existing command display
    const existingDisplay = packageActions.querySelector('.command-display');
    if (existingDisplay) {
        existingDisplay.remove();
    }
    
    // Create and add the command display
    const commandDisplay = document.createElement('div');
    commandDisplay.className = 'command-display';
    commandDisplay.innerHTML = `
        <div class="command-text">
            <i class="fas fa-check"></i>
            command copied: <code>${escapeHtml(command)}</code>
        </div>
    `;
    packageActions.appendChild(commandDisplay);
    
    // Auto-remove the message after 5 seconds
    setTimeout(() => {
        if (commandDisplay.parentNode) {
            commandDisplay.remove();
        }
    }, 5000);
}

// Display error
function displayError(message) {
    const contentDiv = document.getElementById('packageContent');
    contentDiv.innerHTML = `
        <div class="error-message">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Error</h3>
            <p>${escapeHtml(message)}</p>
        </div>
    `;
}

// Format download count for display
function formatDownloadCount(count) {
    if (count >= 1000000) {
        return (count / 1000000).toFixed(1) + 'M';
    } else if (count >= 1000) {
        return (count / 1000).toFixed(1) + 'K';
    } else {
        return count.toString();
    }
}

// Go to a random package
async function goToRandomPackage() {
    try {
        // Get current package name to avoid redirecting to the same package
        const currentPackageName = getPackageNameFromUrl();
        
        // If no current package name, just get any random package
        if (!currentPackageName) {
            const response = await fetch('/random?count=1');
            if (!response.ok) {
                throw new Error('Failed to fetch random package');
            }
            const data = await response.json();
            if (!data.results || data.results.length === 0) {
                throw new Error('No packages available');
            }
            window.location.href = `/package?name=${encodeURIComponent(data.results[0].name)}`;
            return;
        }
        
        // Try to get a different package (up to 3 attempts)
        for (let attempt = 0; attempt < 3; attempt++) {
            // Fetch multiple random packages to increase chances of finding a different one
            const count = attempt === 0 ? 3 : 10; // Start with 3, then try 10
            const response = await fetch(`/random?count=${count}`);
            
            if (!response.ok) {
                throw new Error('Failed to fetch random package');
            }
            
            const data = await response.json();
            if (!data.results || data.results.length === 0) {
                throw new Error('No packages available');
            }
            
            // Find a package that's different from the current one
            const differentPackage = data.results.find(p => p.name !== currentPackageName);
            
            if (differentPackage) {
                window.location.href = `/package?name=${encodeURIComponent(differentPackage.name)}`;
                return;
            }
        }
        
        // If we still haven't found a different package after 3 attempts,
        // it might mean there's only one package in the registry
        // In this case, redirect to home page instead
        console.log('Could not find a different package, redirecting to home');
        window.location.href = '/';
        
    } catch (error) {
        console.error('Error getting random package:', error);
        // Fallback: redirect to home page
        window.location.href = '/';
    }
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadPackageDetails();
    updateDownloadButtonForOS();
}); 


// Set up event listeners
function setupEventListeners() {
    // Set up random package link
    const randomPackageLink = document.getElementById('randomPackageLink');
    if (randomPackageLink) {
        randomPackageLink.addEventListener('click', function(e) {
            e.preventDefault();
            goToRandomPackage();
        });
    }
    
    // Set up install button
    const installBtn = document.getElementById('installBtn');
    if (installBtn) {
        installBtn.addEventListener('click', installPackage);
    }
}

// Update download button based on OS
function updateDownloadButtonForOS() {
    const userAgent = navigator.userAgent.toLowerCase();
    let filename;
    if (userAgent.includes('windows')) {
        filename = 'main_windows.py';
    } else {
        filename = 'main.py';
    }
    // Update both the main and nav install buttons
    const downloadBtn = document.querySelector('.btn-primary');
    if (downloadBtn) {
        downloadBtn.href = `/download/${filename}`;
    }
    const navInstallBtn = document.getElementById('navInstallBtn');
    if (navInstallBtn) {
        navInstallBtn.href = `/download/${filename}`;
    }
}