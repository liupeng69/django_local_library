import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from catalog.forms import RenewBookForm
from catalog.models import Book, Author, BookInstance, Genre


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    # genres and books that contain a particular word (case insensitive)
    word_to_filter = 'fantasy'
    num_books_filter = BookInstance.objects.filter(
        Q(book__genre__name__icontains=word_to_filter) |
        Q(book__title__icontains=word_to_filter) |
        Q(book__summary__icontains=word_to_filter)).count()
    num_books_filter = num_books_filter

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_books_filter': num_books_filter,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


class BookListView(generic.ListView):
    model = Book
    paginate_by = 2


class BookDetailView(generic.DetailView):
    model = Book


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 2


class AuthorDetailView(generic.DetailView):
    model = Author


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter(borrower=self.request.user)
            .filter(status__exact='o')
            .order_by('due_back')
        )


# Added for challenge
# NOTE: Need to do one of the following:
# - Step 1: Grant permission "Catalog | book instance | Set book as returned" to group "Librarians".
#   - User "libadmin" is a member of this group "Librarians".
# - Step 2: Option 1:
#     - In base_generic.html, use {% if perms.catalog.can_mark_returned %}
#     - In bookinstance_list_borrowed_all.html, use {% if perms.catalog.can_mark_returned %}
# - Step 2: Option 2:
#     - Enable the "Staff stauts" checkbox for this user "libadmin".
#     - In base_generic.html, use {% if user.is_staff %}
#     - In bookinstance_list_borrowed_all.html, use {% if user.is_staff %}
class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    permission_required = ('catalog.can_mark_returned')
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


# NOTE: decorators are processed in order
@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # NOTE
            # While you can also access the form data directly through the request
            # (for example, request.POST['renewal_date'] or request.GET['renewal_date'] if using a GET request),
            # this is NOT recommended. The cleaned data is sanitized, validated, and converted into
            # Python-friendly types.

            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed'))

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)


# NOTE:
# The "create" and "update" views use the same template by default, which will
# be named after your model: model_name_form.html (you can change the suffix to
# something other than _form using the template_name_suffix field in your view,
# for example, template_name_suffix = '_other_suffix')

class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/11/2123'}
    permission_required = 'catalog.add_author'


class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    # Not recommended (potential security issue if more fields added)
    fields = '__all__'
    permission_required = 'catalog.change_author'


# NOTE:
# The "delete" view expects to find a template named with the format
# model_name_confirm_delete.html (again, you can change the suffix using
# template_name_suffix in your view).

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    # reverse_lazy() is a lazily executed version of reverse(), used here
    # because we're providing a URL to a class-based view attribute.
    success_url = reverse_lazy('authors')
    permission_required = 'catalog.delete_author'

    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            return HttpResponseRedirect(
                reverse("author-delete", kwargs={"pk": self.object.pk})
            )


class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    initial = {'language': 'English'}
    permission_required = 'catalog.add_book'


class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = '__all__'
    permission_required = 'catalog.change_book'


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.delete_book'

    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            return HttpResponseRedirect(
                reverse("book-delete", kwargs={"pk": self.object.pk})
            )
