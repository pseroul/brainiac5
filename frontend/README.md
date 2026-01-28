# Brainiac5 Frontend

The front end that allow to interact with ideas and order them.

## Setup

### Developpement
Run the server for debug purpose.

1. Install dependencies on your machine
```bash
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npm install react-router-dom axios lucide-react
```

2. Run the code in debug mode
```bash
npm run dev
```


### installation in production
You can directly compile the code on your server but it requests to install `npm`and `Node.js`.
So it is better to build on your dev machine, then transfer to your server. 

1. Install dependencies on your **machine**:
```bash
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npm install react-router-dom axios lucide-react
npx tailwindcss init -p
```

2. Compile the code on your **machine**:
```bash
npm run build
```
push the result on Github: 
```bash
git commit -m "push built frontend"
git push
```

3. Put the code to production on your **server**:
First, retrieve the code: 
```bash
git commit -m "push built frontend"
git push
```

Then move it to the location served by nginx:
```bash
sudo mkdir /var/www/html/brainiac5/
sudo rm -Rf /var/www/html/brainiac5/*
sudo cp -r frontend/dist/* /var/www/html/brainiac5/
```