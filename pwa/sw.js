// sw.js - Service Worker
// Offline çalışma ve performans iyileştirmeleri

const CACHE_NAME = 'kumes-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/app.js',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png'
];

// Kurulum - Cache'leme
self.addEventListener('install', event => {
  console.log('[SW] Kurulum yapılıyor...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Cache açıldı');
        return cache.addAll(urlsToCache);
      })
  );
});

// Aktifleştirme - Eski cache'leri temizle
self.addEventListener('activate', event => {
  console.log('[SW] Aktifleştiriliyor...');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Eski cache siliniyor:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch - Cache-first strateji
self.addEventListener('fetch', event => {
  // WebSocket isteklerini atla
  if (event.request.url.startsWith('ws://') || event.request.url.startsWith('wss://')) {
    return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache'de varsa onu döndür
        if (response) {
          return response;
        }
        
        // Yoksa network'ten al
        return fetch(event.request)
          .then(response => {
            // Geçerli bir response değilse döndür
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Response'u cache'e ekle
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });
            
            return response;
          });
      })
      .catch(() => {
        // Offline'sa basit bir sayfa göster
        return caches.match('/index.html');
      })
  );
});

// Push Notification desteği (opsiyonel)
self.addEventListener('push', event => {
  const data = event.data.json();
  
  const options = {
    body: data.body,
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    }
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
  console.log('[SW] Bildirime tıklandı');
  
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow('/')
  );
});