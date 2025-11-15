import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './ImageGallery.css';

interface ImageGalleryProps {
  hotel: any;
  onClose: () => void;
}

const ImageGallery: React.FC<ImageGalleryProps> = ({ hotel, onClose }) => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  // Extract all images - Use thumbnails to avoid rate limiting
  const images: string[] = [];
  if (hotel.images && Array.isArray(hotel.images)) {
    hotel.images.forEach((img: any) => {
      if (typeof img === 'string') {
        images.push(img);
      } else if (img.thumbnail) {
        // Prefer thumbnail to avoid Google rate limiting
        images.push(img.thumbnail);
      } else if (img.original) {
        images.push(img.original);
      }
    });
  }

  const nextImage = () => {
    setCurrentImageIndex((prev) => (prev + 1) % images.length);
  };

  const prevImage = () => {
    setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  // Booking link: Use hotel.link if available, otherwise create Google Hotels search URL
  let bookingLink = hotel.link || hotel.offers?.[0]?.link || hotel.booking_link;
  
  // Fallback: Create Google Hotels search URL if no direct link
  if (!bookingLink && hotel.name) {
    const searchQuery = encodeURIComponent(`${hotel.name} ${hotel.city || ''} ${hotel.country || ''}`);
    bookingLink = `https://www.google.com/travel/search?q=${searchQuery}`;
  }
  const pricePerNight = hotel.price_per_night?.extracted_price_before_taxes || 
                        hotel.price_per_night?.extracted_price || 
                        hotel.price_per_night;
  const totalPrice = hotel.total_price?.extracted_price_before_taxes || 
                     hotel.total_price?.extracted_price || 
                     hotel.total_price;

  return (
    <motion.div
      className="gallery-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="gallery-container glass"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button className="gallery-close-btn" onClick={onClose}>
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        {/* Hotel Info Header */}
        <div className="gallery-header">
          <div className="gallery-hotel-info">
            <h2 className="gallery-hotel-name">{hotel.name}</h2>
            {(hotel.city || hotel.country) && (
              <div className="gallery-hotel-location">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
                {[hotel.city, hotel.country].filter(Boolean).join(', ')}
              </div>
            )}
          </div>
          {hotel.rating && (
            <div className="gallery-rating">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
              {hotel.rating}
              {hotel.reviews && <span className="gallery-reviews">({hotel.reviews.toLocaleString()} reviews)</span>}
            </div>
          )}
        </div>

        {/* Image Carousel */}
        {images.length > 0 ? (
          <div className="gallery-carousel">
            <AnimatePresence mode="wait">
              <motion.img
                key={currentImageIndex}
                src={images[currentImageIndex]}
                alt={`${hotel.name} - Image ${currentImageIndex + 1}`}
                className="gallery-main-image"
                loading="lazy"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
              />
            </AnimatePresence>

            {/* Navigation Buttons */}
            {images.length > 1 && (
              <>
                <button className="gallery-nav-btn gallery-prev-btn" onClick={prevImage}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="15 18 9 12 15 6" />
                  </svg>
                </button>
                <button className="gallery-nav-btn gallery-next-btn" onClick={nextImage}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </button>
              </>
            )}

            {/* Image Counter */}
            <div className="gallery-counter">
              {currentImageIndex + 1} / {images.length}
            </div>
          </div>
        ) : (
          <div className="gallery-no-images">
            <p>No images available</p>
          </div>
        )}

        {/* Thumbnail Strip - Show max 10 thumbnails to avoid rate limiting */}
        {images.length > 1 && (
          <div className="gallery-thumbnails">
            {images.slice(0, Math.min(10, images.length)).map((img, index) => (
              <motion.div
                key={index}
                className={`gallery-thumbnail ${index === currentImageIndex ? 'active' : ''}`}
                onClick={() => setCurrentImageIndex(index)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <img src={img} alt={`Thumbnail ${index + 1}`} loading="lazy" />
              </motion.div>
            ))}
            {images.length > 10 && (
              <div className="gallery-thumbnail-more">
                +{images.length - 10} more
              </div>
            )}
          </div>
        )}

        {/* Hotel Details & Booking */}
        <div className="gallery-details">
          <div className="gallery-price-section">
            {pricePerNight && (
              <div className="gallery-price">
                <span className="gallery-price-label">Per Night</span>
                <span className="gallery-price-value">₹{Math.round(pricePerNight).toLocaleString()}</span>
              </div>
            )}
            {totalPrice && (
              <div className="gallery-price">
                <span className="gallery-price-label">Total Price</span>
                <span className="gallery-price-value">₹{Math.round(totalPrice).toLocaleString()}</span>
              </div>
            )}
          </div>

          {hotel.amenities && hotel.amenities.length > 0 && (
            <div className="gallery-amenities">
              <h4 className="gallery-amenities-title">Amenities</h4>
              <div className="gallery-amenities-list">
                {hotel.amenities.map((amenity: string, i: number) => (
                  <span key={i} className="gallery-amenity-tag">{amenity}</span>
                ))}
              </div>
            </div>
          )}

          {hotel.essential_info && hotel.essential_info.length > 0 && (
            <div className="gallery-essential-info">
              <h4 className="gallery-info-title">Essential Information</h4>
              <ul className="gallery-info-list">
                {hotel.essential_info.map((info: string, i: number) => (
                  <li key={i}>{info}</li>
                ))}
              </ul>
            </div>
          )}

          {bookingLink && (
            <motion.a
              href={bookingLink}
              target="_blank"
              rel="noopener noreferrer"
              className="gallery-book-btn"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
              {hotel.link ? 'Visit Hotel Website' : 'View on Google Hotels'}
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
            </motion.a>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default ImageGallery;
