import axios from 'axios';

// Determine API URL based on environment variables
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
});

export const getIdeas = () => api.get('/ideas');
export const getIdeasFromTags = (tags) => api.get(`/ideas/tags/${tags}`);
export const searchIdeas = (subname) => api.get(`/ideas/search/${subname}`);
export const getDescription = (idea) => api.get(`/ideas/${idea}/description`);
export const getTocStructure = () => api.get('/toc/structure');
export const updateTocStructure = () => api.post('/toc/update');

export const getTags = () => api.get('/tags');
export const getIdeasTags = (idea) => api.get(`/ideas/${idea}/tags`);
export const getSimilarIdeas = (idea) => api.get(`/ideas/${idea}/similar`);

export const createIdea = (idea) => api.post('/ideas', idea);
export const createTag = (tag) => api.post('/tags', tag);
export const createRelation = (relation) => api.post('/relations', relation);

export const updateIdea = (name, idea) => api.put(`/ideas/${encodeURIComponent(name)}`, idea);

export const deleteIdea = (name) => api.delete(`/ideas/${name}`);
export const deleteTag = (name) => api.delete(`/tags/${name}`);
export const deleteRelation = (name) => api.delete(`/relations/${name}`);

export const verifyOtp = (credentials) => api.post('/verify-otp', credentials);


export default api;
