# CSHub

## Overview

CSHub is a collaborative learning platform for UWA Computer Science students. It brings together account management, study discussions, Study Buddy sessions, announcements, saved content, search, and profile settings in one web application.

The platform is designed to reduce the friction of using several separate tools for study coordination. Students can ask questions, browse discussions, create or join study sessions, receive session message notifications, and keep track of sessions or forum posts they want to return to later.

## Motivation

Computer Science students often coordinate study through scattered channels such as unit forums, private chats, Discord servers, and informal group messages. This can make it hard to find peers, track useful discussions, or stay aware of relevant course and club announcements.

CSHub focuses on three needs:

1. **Collaborative learning** - students can post questions, reply to discussions, and share study ideas.
2. **Study coordination** - students can create, join, save, and discuss Study Buddy sessions.
3. **Centralised updates** - students can read announcements and see relevant activity from one dashboard.

## Target Users

- UWA Computer Science students
- Lecturers or teaching staff who may publish announcements
- Administrators who manage official notices

## Implemented Features

### 1. Authentication and Account Management

Users can:

- register with a username, email, and password
- log in with username or email
- log out securely
- update account details in settings
- change their password after confirming the current password
- manage notification, study preference, and privacy settings

Passwords are stored as salted hashes rather than plain text.

### 2. Learning Forum

The forum provides a space for study-related discussions.

Users can:

- browse forum threads
- create new threads
- reply to existing threads
- like forum posts
- save useful forum posts
- tag posts by topic
- sort discussions by recent, new, or popular activity

### 3. Study Buddy

Study Buddy helps students coordinate small group study sessions.

Users can:

- create a study session with unit, topic, description, date, time, mode, capacity, and location
- browse available sessions
- join or leave sessions
- save sessions for later
- view joined, saved, and hosted sessions
- open a session detail page
- post messages and replies inside a joined session

### 4. Announcements

The announcements section is used for course reminders, club events, and platform updates.

Users can:

- browse announcements
- open announcement details in a modal
- visually track read announcements in the browser

Administrators can:

- create announcements with category, posted label, title, summary, and details

### 5. Search and Dashboard

The dashboard and search features help users find relevant content.

Users can:

- view a personalised home dashboard
- see joined and saved session counts
- view recent Study Buddy activity
- see notifications for unread messages in joined sessions
- search across forum posts, forum replies, Study Buddy sessions, and Study Buddy messages

### 6. Profile and Settings

Users have a profile and settings area that supports basic personalisation.

Users can:

- view their profile
- edit name, username, email, and bio
- set Study Buddy preferences
- control notification preferences
- control privacy preferences such as whether to show full name, joined sessions, saved sessions, and profile discovery

## Data and Persistence

CSHub uses Flask with SQLAlchemy models for users, forum threads, forum replies, forum tags, announcements, Study Buddy sessions, saved/joined sessions, session messages, and read states.

Database schema changes are managed with Flask-Migrate/Alembic migrations. This makes the schema easier to share across team members and avoids manual table changes during app startup.

## Testing

The project includes both unit tests and Selenium tests.

The unit tests cover key Flask behaviours such as:

- registration and hashed password storage
- login and logout
- access control for protected pages
- settings updates
- Study Buddy creation, joining, leaving, and saving
- search results
- session messages and notifications

The Selenium tests exercise browser workflows against a live Flask test server, including registration, login, Study Buddy session creation, joined sessions, session messaging, and logout.

## User Stories

### Student User Stories

1. **As a student, I want to register and log in so that my study activity is linked to my account.**
2. **As a student, I want to post forum questions and replies so that I can discuss study topics with other students.**
3. **As a student, I want to like and save useful forum posts so that I can return to them later.**
4. **As a student, I want to create or join Study Buddy sessions so that I can study collaboratively with others.**
5. **As a student, I want to save Study Buddy sessions so that I can keep track of sessions I am interested in.**
6. **As a student, I want to post messages inside joined study sessions so that I can coordinate with other participants.**
7. **As a student, I want to search across discussions and sessions so that I can quickly find relevant content.**
8. **As a student, I want to update my profile, preferences, and privacy settings so that the platform reflects how I want to use it.**
9. **As a student, I want to read announcements so that I can stay informed about course, club, and platform updates.**

### Staff and Admin User Stories

10. **As an administrator, I want to publish announcements so that students can see important updates in one place.**
11. **As teaching staff, I want announcements to support course reminders and club event notices so that students do not need to check several disconnected channels.**

## Future Extensions

The current implementation focuses on the core study platform. Possible future extensions include:

- marking a forum reply as the best answer
- dedicated event models with club filters and saved events
- richer moderation tools such as reporting and removing inappropriate content
- more detailed contribution badges and activity analytics
- public profile discovery pages for other students

## Conclusion

CSHub provides a practical web application for collaborative Computer Science study. It combines authentication, discussion, Study Buddy coordination, announcements, saved content, search, notifications, and profile settings into one Flask application backed by maintainable models, migrations, and tests.
