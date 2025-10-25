from django.shortcuts import render
from django.http import FileResponse
from .forms import UploadForm
from .utils import preprocess_and_predict, generate_pdf
import os

visitor_count = 0

def home(request):
    global visitor_count
    visitor_count += 1
    form = UploadForm()  # ✅ create a blank form instance
    return render(request, "mammogram_app/upload.html", {  # ✅ full template path
        "visitors": visitor_count,
        "form": form,  # ✅ pass the form to the template
    })


def predict(request):
    context = {}
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.cleaned_data["image"]
            img_path = f"temp_{img.name}"
            with open(img_path, "wb+") as f:
                for chunk in img.chunks():
                    f.write(chunk)

            label, confidence = preprocess_and_predict(img_path)
            pdf_path = generate_pdf(label, confidence)

            context = {
                "label": label,
                "confidence": confidence,
                "pdf_ready": True,
            }

            os.remove(img_path)
            request.session["pdf_path"] = pdf_path
    else:
        form = UploadForm()

    context["form"] = form
    return render(request, "mammogram_app/result.html", context)


def download_report(request):
    pdf_path = request.session.get("pdf_path", None)
    if not pdf_path or not os.path.exists(pdf_path):
        return render(request, "mammogram_app/error.html", {"message": "PDF not available"})
    return FileResponse(open(pdf_path, "rb"), as_attachment=True, filename="prediction_report.pdf")


def faq(request):
    return render(request, "mammogram_app/faq.html")


def disclaimer(request):
    return render(request, "mammogram_app/disclaimer.html")


def analytics(request):
    return render(request, "mammogram_app/analytics.html", {"visitors": visitor_count})
