import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ImageGallery from './ImageGallery';
import './FormattedMessage.css';

interface FormattedMessageProps {
  content: string;
}

const FormattedMessage: React.FC<FormattedMessageProps> = ({ content }) => {
  const [selectedHotel, setSelectedHotel] = useState<any>(null);
  
  // Split content by data markers
  const textContent = content.split(/__HOTEL_DATA__|__FLIGHT_DATA__|__NEWS_DATA__/)[0].trim();
  
  // Parse structured data sections
  const hotelDataMatch = content.match(/__HOTEL_DATA__\n([\s\S]*?)(?=\n\n__|$)/);
  const flightDataMatch = content.match(/__FLIGHT_DATA__\n([\s\S]*?)(?=\n\n__|$)/);
  const newsDataMatch = content.match(/__NEWS_DATA__\n([\s\S]*?)(?=\n\n__|$)/);
  
  let hotels: any[] = [];
  let flights: any[] = [];
  let news: any[] = [];
  
  try {
    if (hotelDataMatch) hotels = JSON.parse(hotelDataMatch[1]);
  } catch (e) {
    console.error('Failed to parse hotel data:', e);
  }
  
  try {
    if (flightDataMatch) flights = JSON.parse(flightDataMatch[1]);
  } catch (e) {
    console.error('Failed to parse flight data:', e);
  }
  
  try {
    if (newsDataMatch) news = JSON.parse(newsDataMatch[1]);
  } catch (e) {
    console.error('Failed to parse news data:', e);
  }

  // Render text with URLs as clickable links
  const renderTextWithLinks = (text: string) => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = text.split(urlRegex);

    return parts.map((part, index) => {
      if (part.match(urlRegex)) {
        const isImage = /\.(jpg|jpeg|png|gif|webp|svg)(\?.*)?$/i.test(part);
        if (isImage) {
          return (
            <div key={index} className="message-image-preview">
              <img src={part} alt="Preview" />
            </div>
          );
        }
        return (
          <a
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="message-inline-link"
          >
            {part}
          </a>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  // Render hotel card (simpler format like reference)
  const renderHotelCard = (hotel: any, index: number) => {
    // Handle images - they can be array of objects {thumbnail, original} or direct URLs
    let thumbnail = '';
    if (hotel.images && hotel.images.length > 0) {
      const firstImage = hotel.images[0];
      if (typeof firstImage === 'string') {
        thumbnail = firstImage;
      } else if (firstImage.thumbnail) {
        thumbnail = firstImage.thumbnail;
      } else if (firstImage.original) {
        thumbnail = firstImage.original;
      }
    }
    
    const pricePerNight = hotel.price_per_night?.extracted_price_before_taxes || 
                          hotel.price_per_night?.extracted_price || 
                          hotel.price_per_night;
    const totalPrice = hotel.total_price?.extracted_price_before_taxes || 
                       hotel.total_price?.extracted_price || 
                       hotel.total_price;
    // Booking link: Use hotel.link if available, otherwise create Google Hotels search URL
    let bookingLink = hotel.link || hotel.offers?.[0]?.link || hotel.booking_link;
    
    // Fallback: Create Google Hotels search URL if no direct link
    if (!bookingLink && hotel.name) {
      const searchQuery = encodeURIComponent(`${hotel.name} ${hotel.city || ''} ${hotel.country || ''}`);
      bookingLink = `https://www.google.com/travel/search?q=${searchQuery}`;
    }
    
    // Format price display
    const displayPrice = pricePerNight ? `₹${Math.round(pricePerNight)}/night` : 
                         totalPrice ? `₹${Math.round(totalPrice)}` : '';
    
    // Format amenities
    const amenitiesText = hotel.amenities && hotel.amenities.length > 0 
      ? hotel.amenities.slice(0, 2).join(', ')
      : '';

    return (
      <motion.div
        key={index}
        className="data-card glass clickable-card"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.05 }}
        whileHover={{ scale: 1.01 }}
        onClick={() => setSelectedHotel(hotel)}
      >
        {thumbnail && (
          <div className="card-image">
            <img src={thumbnail} alt={hotel.name} loading="lazy" />
            {hotel.rating && (
              <div className="card-rating">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
                {hotel.rating}
              </div>
            )}
          </div>
        )}
        
        <div className="card-content">
          <div className="card-header">
            <h4 className="card-title">{hotel.name}</h4>
            {displayPrice && <span className="card-price">{displayPrice}</span>}
          </div>
          
          {amenitiesText && (
            <div className="card-subtitle">{amenitiesText}</div>
          )}

          {bookingLink && (
            <motion.a
              href={bookingLink}
              target="_blank"
              rel="noopener noreferrer"
              className="card-action-btn"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={(e) => e.stopPropagation()} // Prevent card click when clicking button
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
              {hotel.link ? 'Visit Website' : 'View on Google'}
            </motion.a>
          )}
        </div>
      </motion.div>
    );
  };

  // Render flight card (simpler format like reference)
  const renderFlightCard = (flight: any, index: number) => {
    const airline = flight.airline || flight.carrier || 'Airline';
    const price = flight.price || flight.total_price || '';
    const departure = flight.departure_time || flight.departure || '';
    const route = `${flight.departure_airport || flight.from || ''} → ${flight.arrival_airport || flight.to || ''}`;
    const duration = flight.duration || '';

    return (
      <motion.div
        key={index}
        className="data-card glass"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.05 }}
        whileHover={{ scale: 1.01 }}
      >
        <div className="card-content">
          <div className="card-header">
            <h4 className="card-title">{airline}</h4>
            {price && <span className="card-price">{price}</span>}
          </div>
          
          <div className="card-details">
            {route && <div className="card-detail-item">{route}</div>}
            {duration && <div className="card-detail-item">{duration}</div>}
          </div>
          
          {departure && <div className="card-subtitle">Departure: {departure}</div>}
        </div>
      </motion.div>
    );
  };

  // Render news card (simpler format like reference)
  const renderNewsCard = (article: any, index: number) => {
    const title = article.title || article.headline || 'News Article';
    const source = article.source || article.publisher || '';
    const time = article.time || article.published_at || article.date || '';
    const link = article.link || article.url || '';

    return (
      <motion.div
        key={index}
        className="data-card glass"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.05 }}
        whileHover={{ scale: 1.01 }}
      >
        <div className="card-content">
          <h4 className="card-title">{title}</h4>
          
          <div className="card-meta">
            {source && <span className="card-meta-item">{source}</span>}
            {time && <span className="card-meta-item">{time}</span>}
          </div>

          {link && (
            <motion.a
              href={link}
              target="_blank"
              rel="noopener noreferrer"
              className="card-link"
              whileHover={{ scale: 1.02 }}
            >
              Read More →
            </motion.a>
          )}
        </div>
      </motion.div>
    );
  };

  return (
    <>
      <div className="formatted-message">
        {/* Main text content */}
        {textContent && (
          <div className="message-text-content">
            {renderTextWithLinks(textContent)}
          </div>
        )}

        {/* Structured data sections */}
        {hotels.length > 0 && (
          <div className="data-section">
            <div className="data-section-header">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
              Here's what I found:
            </div>
            <div className="data-cards-grid">
              {hotels.map((hotel, index) => renderHotelCard(hotel, index))}
            </div>
          </div>
        )}

        {flights.length > 0 && (
          <div className="data-section">
            <div className="data-section-header">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z" />
              </svg>
              Here's what I found:
            </div>
            <div className="data-cards-grid">
              {flights.map((flight, index) => renderFlightCard(flight, index))}
            </div>
          </div>
        )}

        {news.length > 0 && (
          <div className="data-section">
            <div className="data-section-header">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2" />
                <path d="M18 14h-8" />
                <path d="M15 18h-5" />
                <path d="M10 6h8v4h-8V6Z" />
              </svg>
              Here's what I found:
            </div>
            <div className="data-cards-grid">
              {news.map((article, index) => renderNewsCard(article, index))}
            </div>
          </div>
        )}
      </div>

      {/* Image Gallery Modal */}
      <AnimatePresence>
        {selectedHotel && (
          <ImageGallery hotel={selectedHotel} onClose={() => setSelectedHotel(null)} />
        )}
      </AnimatePresence>
    </>
  );
};

export default FormattedMessage;
