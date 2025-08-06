# AgentSDR - Sales Development Representative Assistant

An AI-powered sales development platform that augments Sales Development Representatives and Sales Managers with intelligent automation, lead management, and real-time insights. Built with Flask backend and Supabase database, designed for enterprise sales teams.

## 🚀 Features

- **Daily Briefing Engine**: Personalized morning digests with lead priorities
- **Follow-Up Management**: Automated prospect tracking and engagement
- **Proposal Generation**: Dynamic proposal creation with AI assistance
- **Opportunity Intelligence**: AI-powered deal insights and recommendations
- **Meeting Preparation**: Intelligent pre-meeting briefings and context
- **CRM Synchronization**: Seamless integration with major CRM platforms
- **WhatsApp Integration**: Mobile alerts and notifications
- **Enterprise Security**: Role-based access with data isolation

## 🏗️ Architecture

```
Frontend (Vanilla JS) → Flask API → Supabase (PostgreSQL + Auth)
```

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python Flask with RESTful API
- **Database**: Supabase (PostgreSQL with real-time features)
- **Authentication**: Supabase Auth with JWT
- **Deployment**: Manus Platform ready

## 📋 Prerequisites

- Python 3.8+
- Supabase account and project
- Modern web browser

## ⚡ Quick Start

### Setup Instructions

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

3. **Set up Supabase**:
   - Create a Supabase project
   - Run `supabase_schema.sql` in SQL Editor
   - Create admin user in Auth

4. **Start the application**:
   ```bash
   python main.py
   ```

5. **Access the platform**:
   - Open http://localhost:5000
   - Login with: admin@agentsdr.com / AgentSDR@2024

## 📁 Project Structure

```
clinivooice/
├── main.py                 # Flask application with Supabase integration
├── static/
│   └── landing.html       # Modern landing page with enterprise signup
├── supabase_schema.sql    # Database schema and RLS policies
├── requirements.txt       # Python dependencies
├── test_connection.py     # Connection testing utility
├── .env.example          # Environment variables template
├── SETUP_GUIDE.md        # Detailed setup instructions
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables (.env)

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SECRET_KEY=your-secret-key
```

### Database Schema

The platform uses the following main tables:
- `organizations` - Sales organization data
- `users` - Sales team members and roles
- `leads` - Prospect and lead information
- `opportunities` - Sales opportunities and pipeline
- `activities` - Sales activities and follow-ups
- `proposals` - Generated proposals and templates
- `meetings` - Meeting preparation and notes

## 🔐 Security Features

- **Row Level Security (RLS)**: Database-level access control
- **JWT Authentication**: Secure token-based auth
- **Role-based Permissions**: Super admin, admin, and user roles
- **Data Isolation**: Multi-tenant architecture
- **Indian Data Residency**: Compliant with local regulations

## 📊 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user

### Enterprises
- `GET /api/enterprises` - List enterprises
- `POST /api/enterprises` - Create enterprise
- `PUT /api/enterprises/<id>` - Update enterprise
- `DELETE /api/enterprises/<id>` - Delete enterprise

### Users
- `GET /api/users` - List users
- `POST /api/users` - Create user
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Delete user

### Dashboard
- `GET /api/stats` - Get dashboard statistics

## 🧪 Testing

### Demo Credentials
- **Email**: admin@agentsdr.com
- **Password**: AgentSDR@2024

### Test Scenarios
1. Login with demo credentials
2. Create new organization
3. Add users to organization
4. Verify dashboard statistics update
5. Test role-based access control

## 🚀 Deployment

### Development
```bash
python main.py
```

### Production
```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Manus Platform
The application is configured for deployment on Manus platform with proper static file serving.

## 🔄 Phase Roadmap

### ✅ Phase 1: Foundation (Complete)
- Flask backend with sales-focused CRUD operations
- Sales dashboard and lead management
- User authentication and role management

### 🔄 Phase 2: Core SDR Features (In Progress)
- Daily Briefing Engine implementation
- Follow-Up Management System
- Basic CRM synchronization
- WhatsApp integration for notifications

### 📋 Phase 3: AI Intelligence (Planned)
- Opportunity Intelligence Radar
- Meeting Preparation Intelligence
- Proposal Generation System
- Advanced analytics and insights

### 📋 Phase 4: Enterprise Features (Planned)
- Advanced CRM integrations
- Team collaboration features
- Mobile app support
- Advanced reporting and analytics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For setup issues or questions:
1. Check the `SETUP_GUIDE.md` for detailed instructions
2. Verify Supabase configuration and credentials
3. Check browser console for frontend errors
4. Review Flask logs for backend issues

## 📄 License

Copyright © 2024 BETTROI. All rights reserved.

## 🙏 Acknowledgments

- **Supabase** - Backend-as-a-Service platform
- **Flask** - Python web framework
- **OpenAI** - AI and natural language processing
- **WhatsApp Business API** - Mobile communication

---

**Made with ❤️ by BETTROI | Transforming Sales Through Intelligent Automation**
