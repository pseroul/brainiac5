audit-backend:
	cd backend && $(MAKE) audit

audit-frontend:
	cd frontend && npm run validate

audit-all: audit-backend audit-frontend