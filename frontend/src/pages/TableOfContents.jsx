import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, BookOpen, ChevronRight, Loader2, X } from 'lucide-react';
import { getTocStructure } from '../services/api';

// Modal component for showing full content
const FullContentModal = ({ isOpen, onClose, content, title }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black bg-opacity-70">
      <div className="bg-white rounded-2xl p-6 w-full max-w-2xl shadow-2xl border border-gray-100 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-xl font-bold text-gray-900">{title}</h2>
          <button 
            onClick={onClose} 
            type="button" 
            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X size={24} className="text-gray-400" />
          </button>
        </div>
        <div className="prose max-w-none">
          <p className="whitespace-pre-wrap text-gray-700 leading-relaxed">
            {content}
          </p>
        </div>
        <div className="mt-6 flex justify-end">
          <button 
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

// Recursive component to render hierarchical structure
const TocItem = ({ item, level = 1, onShowFullContent }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  
  const hasChildren = item.children && item.children.length > 0;
  
  if (item.type === 'heading') {
    return (
      <div className="border-b border-gray-100 last:border-0">
        <div 
          className="flex items-center justify-between p-4 rounded-lg hover:bg-gray-50 transition-colors group cursor-pointer"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center gap-4">
            <span className="text-sm font-mono text-gray-400 w-6">
              {String(level).padStart(2, '0')}
            </span>
            <div>
              <span className="text-lg font-medium text-gray-800 group-hover:text-blue-700 transition-colors">
                {item.title}
              </span>
              {item.originality && (
                <span className="text-xs text-gray-500 ml-2 block">
                  Originality:{item.originality}
                </span>
              )}
              {hasChildren && (
                <span className="text-xs text-gray-500 ml-2">
                  ({item.children.length} items)
                </span>
              )}
            </div>
          </div>
          {hasChildren && (
            <ChevronRight 
              size={18} 
              className={`text-gray-300 group-hover:text-blue-400 transition-transform ${
                isExpanded ? 'rotate-90' : ''
              }`} 
            />
          )}
        </div>
        {hasChildren && isExpanded && (
          <div className="ml-8 pl-4 border-l border-gray-200">
            {item.children.map((child, index) => (
              <TocItem 
                key={child.id || index} 
                item={child} 
                level={level + 1} 
                onShowFullContent={onShowFullContent}
              />
            ))}
          </div>
        )}
      </div>
    );
  } else {
    // Display idea item
    return (
      <div 
        className="flex items-center justify-between p-4 rounded-lg hover:bg-gray-50 transition-colors group cursor-pointer border-b border-gray-50 last:border-0"
        onClick={() => onShowFullContent(item.title, item.text)}
      >
        <div className="flex items-center gap-4">
          <span className="text-sm font-mono text-gray-400 w-6">
            {String(level).padStart(2, '0')}
          </span>
          <div>
            <span className="text-lg font-medium text-gray-800 group-hover:text-blue-700 transition-colors">
              {item.title}
            </span>
            {item.text && (
              <p className="text-sm text-gray-600 mt-1 max-w-md line-clamp-2">
                {item.text}
              </p>
            )}
            <span className="text-xs text-gray-500 mt-1 block">
              Originality:{item.originality}
            </span>
          </div>
        </div>
        <ChevronRight size={18} className="text-gray-300 group-hover:text-blue-400" />
      </div>
    );
  }
};

const TableOfContents = () => {
  const [tocStructure, setTocStructure] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [modalContent, setModalContent] = useState({ title: '', text: '' });

  useEffect(() => {
    const fetchTocStructure = async () => {
      try {
        const response = await getTocStructure();
        setTocStructure(response.data);
      } catch (error) {
        console.error("Erreur lors de la récupération de la structure :", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchTocStructure();
  }, []);

  const handleShowFullContent = (title, text) => {
    setModalContent({ title, text });
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setModalContent({ title: '', text: '' });
  };

  return (
    <div className="min-h-screen bg-white p-4 md:p-12">
      <div className="max-w-3xl mx-auto">
        
        {/* Navigation de retour */}
        <Link 
          to="/dashboard" 
          className="flex items-center gap-2 text-gray-500 hover:text-blue-600 transition-colors mb-8 group"
        >
          <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
          <span>Back to Dashboard</span>
        </Link>

        {/* Titre de la page */}
        <div className="flex items-center gap-4 mb-12 border-b border-gray-100 pb-6">
          <div className="bg-blue-50 p-3 rounded-full text-blue-600">
            <BookOpen size={28} />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Table of contents</h1>
            <p className="text-gray-500 italic">{tocStructure.length} sections</p>
          </div>
        </div>

        {/* Liste des idées */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="animate-spin text-blue-600" size={32} />
          </div>
        ) : (
          <div className="space-y-1">
            {tocStructure.length > 0 ? (
              tocStructure.map((item, index) => (
                <TocItem 
                  key={item.id || index} 
                  item={item} 
                  level={1} 
                  onShowFullContent={handleShowFullContent}
                />
              ))
            ) : (
              <p className="text-center text-gray-400 py-10">No ideas for now.</p>
            )}
          </div>
        )}
      </div>

      {/* Full Content Modal */}
      <FullContentModal 
        isOpen={showModal}
        onClose={handleCloseModal}
        content={modalContent.text}
        title={modalContent.title}
      />
    </div>
  );
};

export default TableOfContents;
