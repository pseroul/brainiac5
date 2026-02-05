import React, { useState, useEffect } from 'react';
import { LogOut, Plus, Search, Trash2, Edit3, Loader2, Lightbulb } from 'lucide-react';
import { getIdeas, createIdea, deleteIdea, updateIdea, createRelation, createTag, getSimilarIdeas } from '../services/api';
import IdeaModal from '../components/IdeaModal';

const Dashboard = () => {
  // États pour les données et l'affichage
  const [ideas, setIdeas] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [editingIdea, setEditingIdea] = useState(null);
  const [similarIdeas, setSimilarIdeas] = useState([]);
  const [isSearchingSimilar, setIsSearchingSimilar] = useState(false);
  const [showSimilarResults, setShowSimilarResults] = useState(false);

  // Charger les idées au démarrage
  useEffect(() => {
    fetchIdeas();
  }, []);

  const fetchIdeas = async () => {
    try {
      setIsLoading(true);
      const response = await getIdeas();
      setIdeas(response.data);
    } catch (error) {
      console.error("Erreur lors de la récupération :", error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSimilarIdeas = async (term) => {
    if (!term.trim()) return;
    
    try {
      setIsSearchingSimilar(true);
      const response = await getSimilarIdeas(term);
      setSimilarIdeas(response.data);
      setShowSimilarResults(true);
    } catch (error) {
      console.error("Erreur lors de la récupération des idées similaires :", error);
      setSimilarIdeas([]);
      setShowSimilarResults(true);
    } finally {
      setIsSearchingSimilar(false);
    }
  };

  const handleSaveIdea = async (formData) => {
  try {
    if (editingIdea) {
      await updateIdea(encodeURIComponent(editingIdea.name), formData);
    } else {
      await createIdea(formData);
    }

    fetchIdeas();
    setIsModalOpen(false);
    setEditingIdea(null);
  } catch (error) {
    console.error("Erreur complète :", error.response?.data);
    // Affichons l'erreur exacte de FastAPI pour comprendre
    const detail = error.response?.data?.detail;
    alert("Erreur 422 : " + JSON.stringify(detail));
  }
};

const handleDelete = async (id) => {
if (window.confirm("Supprimer cette idée ?")) {
    await deleteIdea(id);
    fetchIdeas();
}
};

  // Filtrage des idées en fonction de la recherche
  const filteredIdeas = showSimilarResults 
    ? similarIdeas // Afficher uniquement les idées similaires quand le bouton "Similar" est cliqué
    : ideas.filter(idea => {
        const name = idea.name ? idea.name.toLowerCase() : "";
        const description = idea.description ? idea.description.toLowerCase() : "";
        const search = searchTerm.toLowerCase();
        return name.includes(search) || description.includes(search);
      });

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      {/* Header avec Barre de recherche et Bouton Ajouter */}
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row gap-4 justify-between items-center mb-8">

        <h1 className="text-2xl font-bold text-gray-800">Ideas</h1>

        <div className="flex w-full md:w-auto gap-2">
          {/* Search menu */}
          <div className="relative flex-grow">
            <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
            <input 
              type="text"
              placeholder="Search..."
              className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              onChange={(e) => {
                setSearchTerm(e.target.value);
                if (showSimilarResults) {
                  setShowSimilarResults(false);
                }
              }}
            />
          </div>
          {/* Similar ideas button */}
          <button 
            onClick={() => fetchSimilarIdeas(searchTerm)}
            disabled={!searchTerm.trim() || isSearchingSimilar}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white p-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            {isSearchingSimilar ? (
              <Loader2 className="animate-spin" size={20} />
            ) : (
              <Lightbulb size={20} />
            )}
            <span className="hidden md:inline">Similar</span>
          </button>
          {/* New idea */}
          <button 
            onClick={() => { setEditingIdea(null); setIsModalOpen(true); }}
            className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Plus size={20} />
            <span className="hidden md:inline">New</span>
          </button>
        </div>
      </div>

      {/* Grille d'idées */}
      {isLoading ? (
        <div className="flex justify-center py-20"><Loader2 className="animate-spin text-blue-600" /></div>
      ) : (
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredIdeas.map((idea) => (
            <div key={idea.name} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <h3 className="font-semibold text-lg text-gray-900">{idea.name}</h3>
                <div className="flex gap-2">
                  <button onClick={() => { setEditingIdea(idea); setIsModalOpen(true); }} className="text-gray-400 hover:text-blue-600">
                    <Edit3 size={18} />
                  </button>
                  <button onClick={() => handleDelete(idea.name)} className="text-gray-400 hover:text-red-500">
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
              <p className="text-gray-600 text-sm leading-relaxed">{idea.description}</p>
              {idea.tags && typeof idea.tags === 'string' && idea.tags.trim().length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2 p-2 rounded">
                  <span className="text-xs font-medium text-green-700">TAGS:</span>
                  {idea.tags.split(';').map((tag, index) => {
                    const trimmedTag = tag.trim();
                    return trimmedTag ? (
                      <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                        {trimmedTag}
                      </span>
                    ) : null;
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Modal pour Création / Edition */}
      <IdeaModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onSave={handleSaveIdea}
        initialData={editingIdea}
      />
    </div>
  );
};

export default Dashboard;