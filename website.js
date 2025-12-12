const gallery = document.getElementById('gallery');
const btnNormal = document.getElementById('btn-normal');
const btnSnow = document.getElementById('btn-snow');
const btnRain = document.getElementById('btn-rain');

const modal = document.getElementById('imageModal');
const modalImg = document.getElementById("img01");
const loader = document.getElementById('loader');
const sentinel = document.getElementById('sentinel');

// Helper functions
const getBaseName = (filename) => filename.replace(/\.[^/.]+$/, "");

// === Modal Logic ===
function openModal(imgSrc) {
    modal.style.display = "flex";
    modalImg.src = imgSrc;
}
function closeModal() { modal.style.display = "none"; }
document.addEventListener('keydown', (e) => { if (e.key === "Escape") closeModal(); });

// === Infinite Scroll Logic ===
let currentFiles = [];
let loadedCount = 0;
let currentDatasetType = 'normal'; 
// CHANGE 1: Increase Batch Size to 12. 
// 4 is too small for big monitors; 12 ensures the screen fills up.
const BATCH_SIZE = 12; 
let observer;
let isLoading = false;

const observerOptions = {
    root: null,
    rootMargin: '100px',
    threshold: 0.1
};

const handleIntersect = (entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !isLoading) {
            renderNextBatch();
        }
    });
};

function switchDataset(type) {
    currentDatasetType = type;

    // Update Buttons UI
    [btnNormal, btnSnow, btnRain].forEach(btn => btn.classList.remove('active'));
    
    if (type === 'normal') btnNormal.classList.add('active');
    else if (type === 'snow') btnSnow.classList.add('active');
    else if (type === 'rain') btnRain.classList.add('active');
    
    // Reset Gallery State
    gallery.innerHTML = '';
    loadedCount = 0;
    currentFiles = [];
    
    if (observer) observer.disconnect();
    
    loadGalleryData(type);
}

function loadGalleryData(datasetType) {
    if (typeof GALLERY_DATA === 'undefined') {
        gallery.innerHTML = `<div style="color:red; text-align:center;">Error: gallery_data.js not found.</div>`;
        return;
    }

    currentFiles = GALLERY_DATA[datasetType] || [];
    
    if (currentFiles.length === 0) {
        gallery.innerHTML = `<p style="color:#666;">No images found for ${datasetType}.</p>`;
        return;
    }

    observer = new IntersectionObserver(handleIntersect, observerOptions);
    observer.observe(sentinel);
    
    // Initial load
    renderNextBatch(); 
}

function renderNextBatch() {
    if (loadedCount >= currentFiles.length) {
        loader.style.display = 'none';
        return;
    }

    isLoading = true;
    loader.style.display = 'block';

    const nextBatch = currentFiles.slice(loadedCount, loadedCount + BATCH_SIZE);

    nextBatch.forEach(filename => {
        // Path logic matches your folder structure
        const photoPath = `inference/${currentDatasetType}/overall/previews/${filename}`;        
        const labelPath = `labels/${currentDatasetType}/${getBaseName(filename)}.txt`;
        
        createCard(filename, photoPath, labelPath);
    });

    loadedCount += nextBatch.length;
    loader.style.display = 'none';
    
    // Allow a tiny delay for DOM paint, then release lock and check if we need more
    setTimeout(() => {
        isLoading = false;
        checkIfShouldLoadMore();
    }, 50);
}

function checkIfShouldLoadMore() {
    // If we still have files...
    if (loadedCount < currentFiles.length) {
        const sentinelRect = sentinel.getBoundingClientRect();
        // Check if the sentinel is STILL visible on screen (meaning we have empty space)
        if (sentinelRect.top <= window.innerHeight) {
            renderNextBatch();
        }
    }
}

function createCard(fileName, photoPath) {
    const card = document.createElement('div');
    card.className = 'card';

    const header = document.createElement('div');
    header.className = 'card-header';
    header.innerText = fileName;

    const img = document.createElement('img');
    img.src = photoPath; 
    img.loading = "lazy"; 
    img.alt = fileName;
    img.onclick = () => openModal(img.src);

    card.appendChild(header);
    card.appendChild(img);
    gallery.appendChild(card);
}

// Initialize with 'normal'
switchDataset('normal');