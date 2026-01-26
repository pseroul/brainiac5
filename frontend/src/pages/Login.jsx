import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, ShieldCheck, LogIn } from 'lucide-react';

const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [otpCode, setOtpCode] = useState('');

const handleLogin = async (e) => {
  e.preventDefault();
  
  try {
    const response = await fetch('http://localhost:8000/verify-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, otp_code: otpCode }),
    });

    if (response.ok) {
      localStorage.setItem('isAuthenticated', 'true');
      navigate('/dashboard');
    } else {
      alert("Code Google Authenticator incorrect");
    }
  } catch (error) {
    alert("Erreur de connexion au serveur");
  }
};

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
        
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-50 rounded-full mb-4">
            <ShieldCheck className="text-blue-600" size={32} />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Accès Sécurisé</h2>
          <p className="text-gray-500 mt-2 text-sm">Entrez votre code Google Authenticator</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          {/* Champ Email */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 ml-1">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 text-gray-400" size={20} />
              <input 
                type="email" 
                placeholder="votre@email.com" 
                className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all bg-gray-50"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Champ Code Authenticator */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 ml-1">Code à 6 chiffres</label>
            <div className="relative">
              <ShieldCheck className="absolute left-3 top-3 text-gray-400" size={20} />
              <input 
                type="text" 
                inputMode="numeric"
                maxLength="6"
                placeholder="000 000" 
                className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-600 focus:outline-none transition-all bg-gray-50 text-center text-2xl tracking-[0.5em] font-mono"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))} // Garde uniquement les chiffres
                required
              />
            </div>
          </div>

          <button 
            type="submit" 
            className="w-full bg-gray-900 hover:bg-black text-white font-bold py-4 rounded-xl flex items-center justify-center gap-2 transition-all transform hover:scale-[1.02] active:scale-95 shadow-lg"
          >
            <LogIn size={20} />
            Vérifier et Entrer
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 mt-8">
          Système de protection par jeton temporel (TOTP)
        </p>
      </div>
    </div>
  );
};

export default Login;