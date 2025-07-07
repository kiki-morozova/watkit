// API base URL - since we're serving from the same server
const API_BASE_URL = '';

// DOM elements
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const randomBtn = document.getElementById('randomBtn');
const navInstallBtn = document.getElementById('navInstallBtn');
const packagesGrid = document.getElementById('packagesGrid');
const loadingPackages = document.getElementById('loadingPackages');
const noPackages = document.getElementById('noPackages');
const codePreview = document.getElementById('codePreview');
const searchResults = document.getElementById('searchResults');

// Load packages on page load
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    // Show code preview by default
    showCodePreview();
    // Load download count
    loadDownloadCount();
    // Update download button based on OS
    updateDownloadButtonForOS();
});

// Detect OS and update download button
function updateDownloadButtonForOS() {
    const userAgent = navigator.userAgent.toLowerCase();
    console.log(`userAgent: ${userAgent}`);
    let filename;
    
    if (userAgent.includes('windows')) {
        filename = 'main_windows.py';
    } else {
        // For macOS, Linux, and other non-Windows systems
        filename = 'main.py';
    }
    
    // Update both the main and nav install buttons
    const downloadBtn = document.querySelector('.btn-primary');
    if (downloadBtn) {
        downloadBtn.href = `/download/${filename}`;
    }
    if (navInstallBtn) {
        navInstallBtn.href = `/download/${filename}`;
    }
}

// Set up event listeners
function setupEventListeners() {
    searchBtn.addEventListener('click', performSearch);
    randomBtn.addEventListener('click', getRandomPackages);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // Real-time search as user types
    searchInput.addEventListener('input', debounce(function() {
        const query = searchInput.value.trim();
        if (query === '') {
            showCodePreview();
        } else {
            performSearch();
        }
    }, 300));
}

// Load packages from the API
async function loadPackages() {
    try {
        showLoading(true);
        
        // Load specific default packages: math_utils and algebra
        const defaultPackages = ['math_utils', 'algebra'];
        const allResults = [];
        
        for (const packageName of defaultPackages) {
            try {
                const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(packageName)}&by=name`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.results && data.results.length > 0) {
                        allResults.push(...data.results);
                    }
                }
            } catch (error) {
                console.error(`Error loading package ${packageName}:`, error);
            }
        }
        
        console.log('Loaded default packages:', allResults);
        displayPackages(allResults);
        
    } catch (error) {
        console.error('Error loading packages:', error);
        displayError('Failed to load packages. Please try again later.');
    } finally {
        showLoading(false);
    }
}

// Perform search
async function performSearch() {
    const query = searchInput.value.trim();
    
    if (!query) {
        showCodePreview();
        return;
    }
    
    try {
        showSearchResults();
        showLoading(true);
        
        const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}&by=name`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Search results for "' + query + '":', data);
        displayPackages(data.results || []);
        
    } catch (error) {
        console.error('Error searching packages:', error);
        displayError('Search failed. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Get random packages
async function getRandomPackages() {
    try {
        showSearchResults();
        showLoading(true);
        
        const response = await fetch(`${API_BASE_URL}/random?count=3`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Random packages found:', data);
        displayPackages(data.results || []);
        
    } catch (error) {
        console.error('Error getting random packages:', error);
        displayError('Failed to get random packages. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Load download count
async function loadDownloadCount() {
    try {
        const response = await fetch(`${API_BASE_URL}/downloads`);
        if (response.ok) {
            const data = await response.json();
            document.getElementById('downloadCount').textContent = data.total_downloads;
        }
    } catch (error) {
        console.error('Error loading download count:', error);
        // Keep the default value if we can't load it
    }
}

// Display packages in the grid
function displayPackages(packages) {
    console.log('Displaying packages:', packages);
    
    if (packages.length === 0) {
        packagesGrid.innerHTML = '';
        noPackages.style.display = 'block';
        return;
    }
    
    noPackages.style.display = 'none';
    
    const packagesHTML = packages.map(package => createPackageCard(package)).join('');
    packagesGrid.innerHTML = packagesHTML;
    
    // Add click event listeners to package cards
    const packageCards = packagesGrid.querySelectorAll('.package-card');
    packageCards.forEach(card => {
        card.addEventListener('click', function() {
            const packageName = this.getAttribute('data-package-name');
            console.log('Clicked on package:', packageName);
            window.location.href = `/package?name=${encodeURIComponent(packageName)}`;
        });
    });
}

// Create a package card HTML
function createPackageCard(package) {
    const name = package.name || 'Unknown Package';
    const author = package.author || 'Unknown Author';
    const latestVersion = package.latest || '1.0.0';
    const downloads = package.downloads || 0;
    
    // Format download count
    const formattedDownloads = formatDownloadCount(downloads);
    
    return `
        <div class="package-card" data-package-name="${escapeHtml(name)}" style="cursor: pointer;">
            <div class="package-name">${escapeHtml(name)}</div>
            <div class="package-author">by ${escapeHtml(author)}</div>
            <div class="package-version">v${escapeHtml(latestVersion)}</div>
            <div class="package-downloads">
                <i class="fas fa-download"></i>
                ${formattedDownloads}
            </div>
            <div class="package-description">
                Latest version available
            </div>
        </div>
    `;
}

// Show/hide code preview and search results
function showCodePreview() {
    codePreview.style.display = 'block';
    searchResults.style.display = 'none';
}

function showSearchResults() {
    codePreview.style.display = 'none';
    searchResults.style.display = 'block';
}

// Show/hide loading state
function showLoading(show) {
    if (show) {
        loadingPackages.style.display = 'block';
        packagesGrid.style.display = 'none';
    } else {
        loadingPackages.style.display = 'none';
        packagesGrid.style.display = 'flex';
    }
}

// Display error message
function displayError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        background-color: rgba(0, 5, 5, 0.5);
        border-left: 4px solid #A3C4BC;
        padding: 15px;
        margin: 15px 0;
        color: #CFD6EA;
        border-radius: 4px;
        text-align: center;
        font-family: 'recmonocasual', sans-serif;
    `;
    errorDiv.textContent = message;
    
    packagesGrid.parentNode.insertBefore(errorDiv, packagesGrid);
    
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 5000);
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

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
} 