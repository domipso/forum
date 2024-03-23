from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm, \
    MessageForm, ThreadForm
from app.models import User, Post, Message, Notification, Thread
from app.translate import translate
from app.main import bp
from flask import abort

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/threads', methods=['GET', 'POST'])#Route wurde auf Threads als Startseite geändert
@login_required
def index():
    form = ThreadForm()  # Ein Objekt wird erstellt, um Formulardaten zu verarbeiten (Daten kommen aus Threads.HTML)
    if form.validate_on_submit():  # Überprüft, ob das Formular beim Absenden gültig ist
        thread = Thread(title=form.thread.data, creator=current_user)  # Erstellt einen neuen Thread mit den Formulardaten und dem aktuellen Benutzer als Ersteller
        db.session.add(thread)  # Fügt den neuen Thread der Datenbank hinzu
        db.session.commit()  # Commited die ÄNderungen in der Datenbank
        flash(_('Your thread is now live!'))  # Zeigt die Meldung an
        return redirect(url_for('main.index'))  # Leitet den Benutzer zur Hauptseite um
    threads = current_user.all_threads()  # Ruft alle Threads des aktuellen Benutzers ab
    return render_template('threads.html', title=_('Home'), form=form, threads=threads)  # Zeigt 'threads.html' wieder an


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('threads.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)

@bp.route('/threads/<int:id>/posts', methods=['GET', 'POST'])
@login_required
def thread_posts(id): 
    thread = Thread.query.get_or_404(id)# Thread anhand der ID aus der Datenbank abrufen oder 404-Fehler auslösen
    form = PostForm()# Erstellen eines PostFormulars
    if form.validate_on_submit(): # Überprüfen, ob das Formular erfolgreich übermittelt wurde    
        post = Post(body=form.post.data, thread_id=id, author=current_user)# Erstellen eines neuen Posts aus den Formulardaten
        db.session.add(post)# Post zur Datenbank hinzufügen und speichern
        db.session.commit()
        thread.last_update = datetime.utcnow()# Aktualisieren des last_update-Attributs des Threads
        db.session.commit()  # Speichern der Änderungen am Thread
        flash(_('Your post is now live!'))# Nachricht anzeigen, dass der Beitrag erfolgreich erstellt wurde
        return redirect(url_for('main.thread_posts', id=id))# Weiterleitung zur Seite mit den Posts des Threads
    posts = thread.posts.all()# Alle Posts des Threads 
    # Rendern der Vorlage und Übergeben der Daten an das Template
    return render_template('thread_posts.html', thread=thread, posts=posts, form=form)

@bp.route('/threads/delete/<int:id>', methods=['POST']) #route zum löschen von threads
@login_required
def delete_thread(id):
    thread = Thread.query.get_or_404(id)
    # Überprüfen, ob der aktuelle Benutzer ein Admin ist
    if not current_user.is_admin:
        flash(_('You are not allowed to delete threads.'))
        return redirect(url_for('main.index'))
    db.session.delete(thread)  #Thread löschen 
    db.session.commit()# Speichern der Änderungen in der Datenbank
    flash(_('The thread has been deleted.'))# Erfolgsmeldung über das Löschen des Threads
    return redirect(url_for('main.index'))

@bp.route('/posts/delete/<int:id>', methods=['POST']) # Route zum Löschen von Posts
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)  # Abrufen des zu löschenden Beitrags aus der Datenbank oder der Anzeige, dass nichts gefunden wurde. Wird in diesem Setiing jedoch eher selten vorkommen.
    if not current_user.is_admin: # Überprüfen, ob der aktuelle Benutzer ein Administrator ist
        flash(_('Du bist nicht berechtigt, Beiträge zu löschen.'))  # Fehlermeldung, falls der Benutzer kein Admin ist
        return redirect(url_for('main.index'))  # Umleitung zur Startseite
    db.session.delete(post)  # Löschen des Beitrags aus der Datenbank
    db.session.commit()  # Speichern der Änderungen in der Datenbank
    flash(_('The post has been deleted'))  # Erfolgsmeldung über das Löschen des Beitrags
    return redirect(url_for('main.index'))  # Umleitung zur Startseite nach dem Löschen

@bp.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    if not current_user.is_admin:
        abort(403)  # 403 Fehler, wenn der Benutzer kein Admin ist
    users = User.query.all()#Ruft alle Benutzer ab 
    return render_template('show_users.html', users=users)

@bp.route('/admin/users/<int:user_id>/toggle_admin', methods=['POST'])#Macht Benutzer zu Admins 
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        abort(403)  # 403 Fehler, wenn der Benutzer kein Admin ist
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin  # Umkehren des Admin-Status
    db.session.commit()#Commitment in der Datenbank 
    flash('Admin status has been successfuly updated!.')# Erfolgsmeldung anzeigen
    return redirect(url_for('main.admin_users'))# Zurück zur Benutzerübersichtsseite 

@bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        abort(403)  # Verweigert den Zugriff, wenn der Benutzer kein Admin ist (sollte nicht einfach so auf die Seite kommen, sicher ist sicher)
    user = User.query.get_or_404(user_id)  # Den Benutzer anhand der ID suchen oder 404-Fehler auslösen
    db.session.delete(user)  # Benutzer aus der Datenbank entfernen
    db.session.commit()  # Änderungen in der Datenbank speichern
    flash(_('The user has been deleted'))  # Erfolgsmeldung anzeigen
    return redirect(url_for('main.admin_users'))  # Zurück zur Benutzerübersichtsseite umleiten



@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(_('You are following %(username)s!', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_('You are not following %(username)s.', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page=page, per_page=current_app.config['POSTS_PER_PAGE'],
            error_out=False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/export_posts')
@login_required
def export_posts():
    if current_user.get_task_in_progress('export_posts'):
        flash(_('An export task is currently in progress'))
    else:
        current_user.launch_task('export_posts', _('Exporting posts...'))
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
